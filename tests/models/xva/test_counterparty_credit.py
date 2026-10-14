# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A counterparty's credit comes from its own record, not a rating table.

The XVA desk and the PRS pricer both read it through
``models.xva.counterparty_credit``; a record without a Credit block falls back
to the rating proxy and is labelled as derived.
"""

from datetime import date

import pytest

from config.port import DEFAULT_YIELD_CURVE
from config.xva import RATING_CDS_SPREADS, XvaConfig
from models.xva import ZeroCurve, cds_par_spread, desk
from models.xva.counterparty_credit import credit_of, hazard_curve, summary
from port.cdm.ctpy import CounterpartyCDM
from port.cdm.ctpy._credit import credit_errors
from port.src.counterparty._credit import with_credit_curve

ZERO = ZeroCurve(DEFAULT_YIELD_CURVE)


def _record(rating="A", credit=None):
    root = {"Party": {"PartyID": "CTPY-1", "PartyName": "Test Re"},
            "Counterparties": [{"CounterpartyRole": "Party1", "PartyRef": "MKM"},
                               {"CounterpartyRole": "Party2", "PartyRef": "CTPY-1"}],
            "_platform": {"CreditRating": rating, "PartyType": "Insurer"}}
    if credit is not None:
        root["Credit"] = credit
    return {"CounterpartySet": root}


MARKET = {"CdsSpreads": [{"TenorYears": 1, "SpreadBps": 40.0}, {"TenorYears": 3, "SpreadBps": 60.0},
                         {"TenorYears": 5, "SpreadBps": 80.0}],
          "Recovery": 0.35, "Source": "Market", "AsOf": "2026-10-14"}


class TestCreditOf:

    def test_reads_the_records_own_curve(self):
        view = credit_of(_record(credit=MARKET))
        assert view.source == "Market" and not view.derived
        assert view.recovery == 0.35 and view.spread_bps(5) == 80.0 and view.spread_bps(4) == 70.0

    def test_falls_back_to_the_rating_proxy_and_says_so(self):
        view = credit_of(_record("BBB"))
        assert view.derived and view.source == "RatingProxy"
        assert view.spread_bps() == pytest.approx(RATING_CDS_SPREADS["BBB"] * 1e4)

    def test_unknown_rating_uses_the_conservative_proxy(self):
        assert credit_of(None).rating == "BB"

    def test_curve_reprices_every_quote(self):
        view = credit_of(_record(credit=MARKET))
        curve = hazard_curve(view, ZERO)
        for tenor, bps in view.points:
            assert cds_par_spread(curve, ZERO, tenor, 0.35) * 1e4 == pytest.approx(bps, abs=1e-8)

    def test_an_inverted_curve_falls_back_to_its_longest_quote(self):
        bad = dict(MARKET, CdsSpreads=[{"TenorYears": 1, "SpreadBps": 2000.0},
                                       {"TenorYears": 2, "SpreadBps": 10.0}])
        curve = hazard_curve(credit_of(_record(credit=bad)), ZERO)
        assert len(curve.rates) == 1
        assert cds_par_spread(curve, ZERO, 2, 0.35) * 1e4 == pytest.approx(10.0, abs=1e-8)

    def test_summary_for_screens(self):
        s = summary(credit_of(_record(credit=MARKET)))
        assert s == {"cds_5y_bps": 80.0, "recovery": 0.35, "credit_source": "Market",
                     "credit_derived": False, "credit_as_of": "2026-10-14"}


class TestDeskUsesTheRecord:

    def test_market_spread_moves_the_counterparty_hazard(self):
        cfg = XvaConfig(n_paths=500)
        proxy = desk.counterparty_terms(_record("A"), ZERO, cfg)[0]
        market = desk.counterparty_terms(_record("A", credit=MARKET), ZERO, cfg)[0]
        assert market.rates[-1] != proxy.rates[-1]
        assert cds_par_spread(market, ZERO, 5, 0.35) * 1e4 == pytest.approx(80.0, abs=1e-8)

    def test_the_run_records_the_credit_source(self):
        row = {"swap_id": "S1", "gauge_id": "G1", "trigger": "severe", "notional": 5e6,
               "trade_spread_bps": 150.0, "is_payer": True, "counterparty_id": "CTPY-1", "mtm": 0.0,
               "maturity": date(2029, 10, 14).isoformat()}
        out = desk.run_book([row], {"CTPY-1": _record(credit=MARKET)}, {"yield_curve": DEFAULT_YIELD_CURVE},
                            lambda g, t: 0.02, XvaConfig(n_paths=500), date(2026, 10, 14))
        assert out["netting_sets"][0]["credit"]["credit_source"] == "Market"


class TestCdm:

    def test_a_well_formed_block_validates(self):
        assert CounterpartyCDM().validate(_record(credit=MARKET)) == {}

    @pytest.mark.parametrize("bad, message", [
        ({"CdsSpreads": []}, "at least one tenor"),
        ({"CdsSpreads": [{"TenorYears": 0, "SpreadBps": 10}]}, "TenorYears must be"),
        ({"CdsSpreads": [{"TenorYears": 1, "SpreadBps": -5}]}, "SpreadBps must be"),
        ({"CdsSpreads": [{"TenorYears": 3, "SpreadBps": 5}, {"TenorYears": 1, "SpreadBps": 5}]},
         "strictly increasing"),
        ({"CdsSpreads": [{"TenorYears": 1, "SpreadBps": 5}], "Recovery": 1.2}, "Recovery must be"),
        ({"CdsSpreads": [{"TenorYears": 1, "SpreadBps": 5}], "Source": "Broker"}, "Invalid Source"),
    ])
    def test_each_defect_is_reported(self, bad, message):
        assert any(message in e for e in credit_errors({"Credit": bad}))

    def test_absent_block_is_valid(self):
        assert credit_errors({}) == []

    def test_generator_attaches_a_labelled_proxy_curve(self):
        record = with_credit_curve(_record("AA-"))
        credit = record["CounterpartySet"]["Credit"]
        assert credit["Source"] == "RatingProxy"
        assert [p["TenorYears"] for p in credit["CdsSpreads"]] == [1.0, 3.0, 5.0, 7.0]
        assert credit["CdsSpreads"][0]["SpreadBps"] == pytest.approx(RATING_CDS_SPREADS["AA-"] * 1e4)
        assert CounterpartyCDM().validate(record) == {}
