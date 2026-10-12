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

"""The desk adapter (WP4): blotter rows and the counterparty CDM in, netting
sets, per-trade figures, the valuation KPI and an incremental quote out."""

from datetime import date, timedelta
from dataclasses import replace

import pytest

from config.port import DEFAULT_YIELD_CURVE
from config.xva import UNKNOWN_COUNTERPARTY_RATING, XvaConfig
from models.xva import desk
from models.xva.valuation import fair_spread

TODAY = date(2026, 10, 9)
STATE = {"yield_curve": DEFAULT_YIELD_CURVE, "risk_free_rate": 0.03}
FAST = XvaConfig(n_paths=1_000)


def hazard_for(gauge_id, trigger):
    return {"G1": 0.02, "G2": 0.01}.get(gauge_id, 0.015)


def row(swap_id, gauge="G1", payer=True, years=3, cpty="CTPY-A", spread=150.0, mtm=0.0,
        notional=5e6):
    return {"swap_id": swap_id, "gauge_id": gauge, "trigger": "severe", "notional": notional,
            "trade_spread_bps": spread, "is_payer": payer, "counterparty_id": cpty, "mtm": mtm,
            "maturity": (TODAY + timedelta(days=round(365.25 * years))).isoformat()}


def record(party, rating="A", party_type="Insurer", csa="None"):
    return {"CounterpartySet": {
        "Party": {"PartyID": party},
        "_platform": {"CreditRating": rating, "PartyType": party_type},
        "CreditSupport": {"NettingSets": [{"NettingSetID": f"NS-{party}", "CsaType": csa,
                                           "CloseOutNetting": True, "Threshold": 0.0,
                                           "MarginPeriodOfRiskDays": 10}]}}}


class TestAdapters:

    def test_remaining_quarters(self):
        assert desk.remaining_quarters((TODAY + timedelta(days=365)).isoformat(), TODAY) == 1.0
        assert desk.remaining_quarters((TODAY + timedelta(days=20)).isoformat(), TODAY) == 0.25

    def test_closed_and_matured_rows_are_skipped(self):
        assert desk.trade_from_enriched({**row("S"), "notional": 0}, hazard_for, TODAY) is None
        past = {**row("S"), "maturity": (TODAY - timedelta(days=1)).isoformat()}
        assert desk.trade_from_enriched(past, hazard_for, TODAY) is None

    def test_trade_uses_the_flat_gauge_rate(self):
        t = desk.trade_from_enriched(row("S", gauge="G2"), hazard_for, TODAY)
        assert t.gauge_id == "G2" and t.spread == 0.0150 and t.tenor_years == 3.0
        assert t.trigger.rates[0] == pytest.approx(-__import__("math").log(0.99))

    def test_counterparty_terms_from_the_cdm(self):
        zero = desk.zero_curve(STATE)
        _, profile, csa, netting, ns_id, rating = desk.counterparty_terms(
            record("CTPY-A", "BBB-", "Bank", "VM"), zero, FAST)
        assert (profile.exposure_class, profile.sector, rating) == ("bank", "financials", "BBB-")
        assert csa.variation_margin and netting and ns_id == "NS-CTPY-A"

    def test_unknown_counterparty_is_conservative(self):
        _, profile, csa, netting, ns_id, rating = desk.counterparty_terms(
            None, desk.zero_curve(STATE), FAST)
        assert rating == UNKNOWN_COUNTERPARTY_RATING
        assert (profile.exposure_class, profile.sector) == ("corporate", "other")
        assert not csa.variation_margin and ns_id == "NS-UNASSIGNED"

    def test_zero_curve_falls_back_to_the_flat_rate(self):
        assert desk.zero_curve({"risk_free_rate": 0.05}).zero_rate(3.0) == 0.05


class TestTermStructureCurve:
    """Plan §16: one curve per gauge on which every bucket reprices exactly."""

    ZERO = desk.zero_curve(STATE)

    def test_each_bucket_reprices_at_the_front_office_fair_spread(self):
        from models.hazard.prs_analytical import compute_prs_spread
        from models.xva import PrsTrade
        probs = {1: 0.010, 2: 0.012, 3: 0.015, 5: 0.014}
        curve, fell_back = desk.term_structure_curve(probs, self.ZERO)
        assert not fell_back and len(curve.rates) == 4
        for tenor, p in probs.items():
            t = PrsTrade(1e6, 0.01, tenor, True, curve)
            fo = compute_prs_spread(p, tenor, 0.0, yield_curve=DEFAULT_YIELD_CURVE, min_spread_bps=0)
            assert fair_spread(t, self.ZERO) * 1e4 == pytest.approx(fo, rel=1e-10)

    def test_equal_buckets_give_the_flat_curve(self):
        curve, fell_back = desk.term_structure_curve({1: 0.02, 3: 0.02}, self.ZERO)
        assert not fell_back and curve.rates.tolist() == [-__import__("math").log(0.98)]

    def test_no_positive_bucket_means_no_hazard(self):
        curve, _ = desk.term_structure_curve({1: 0.0}, self.ZERO)
        assert curve.rates.tolist() == [0.0]

    def test_an_unbootstrappable_curve_falls_back_flat_and_says_so(self):
        curve, fell_back = desk.term_structure_curve({1: 0.20, 2: 0.01}, self.ZERO)
        assert fell_back and curve.rates.tolist() == [-__import__("math").log(0.99)]

    def test_a_curve_lookup_reaches_the_trade(self):
        curve = desk.term_structure_curve({1: 0.01, 3: 0.02}, self.ZERO)[0]
        t = desk.trade_from_enriched(row("S"), lambda g, trig: curve, TODAY)
        assert t.trigger is curve


class TestRunBook:

    @pytest.fixture(scope="class")
    def book(self):
        rows = [row("S1"), row("S2", gauge="G2", payer=False), row("S3", cpty="CTPY-B", years=2),
                row("S4", cpty=None)]
        cps = {"CTPY-A": record("CTPY-A"), "CTPY-B": record("CTPY-B", "BB+", "Utility")}
        return desk.run_book(rows, cps, STATE, hazard_for, FAST, TODAY)

    def test_one_netting_set_per_counterparty(self, book):
        ids = sorted(s["netting_set_id"] for s in book["netting_sets"])
        assert ids == ["NS-CTPY-A", "NS-CTPY-B", "NS-UNASSIGNED"]
        assert book["summary"]["n_trades"] == 4

    def test_trade_figures_add_up_to_their_netting_set(self, book):
        for s in book["netting_sets"]:
            rows = [t for t in book["trades"] if t["netting_set_id"] == s["netting_set_id"]]
            assert sum(t["xva"] for t in rows) == pytest.approx(s["booked"]["total"]["value"])
            assert sum(t["kva"] for t in rows) == pytest.approx(s["kva"]["total"]["value"])

    def test_summary_and_audit(self, book):
        assert book["summary"]["xva_total"] == pytest.approx(
            sum(s["booked"]["total"]["value"] for s in book["netting_sets"]))
        assert book["summary"]["kva_included_in_booked"] is False
        assert book["audit"]["model_id"] == "MKM-XV-001" and book["audit"]["n_paths"] == 1_000
        assert book["as_of"] == TODAY.isoformat()

    def test_valuation_kpi_flags_a_mismatched_front_office_mtm(self, book):
        assert all("kpi" in t for t in book["trades"])
        bad = desk.run_book([row("S1", mtm=1e6)], {}, STATE, hazard_for, FAST, TODAY)
        assert bad["trades"][0]["kpi"]["breach"] and bad["summary"]["kpi_breaches"] == 1

    def test_closed_trades_are_left_out_of_the_book(self):
        out = desk.run_book([row("S1"), {**row("S2"), "notional": 0}], {}, STATE, hazard_for,
                            FAST, TODAY)
        assert [t["swap_id"] for t in out["trades"]] == ["S1"]

    def test_kpi_passes_when_the_front_office_agrees(self):
        trade = desk.trade_from_enriched(row("S1"), hazard_for, TODAY)
        from models.xva.valuation import value
        v = value(trade, desk.zero_curve(STATE), 0.0)
        out = desk.run_book([row("S1", mtm=v)], {}, STATE, hazard_for, FAST, TODAY)
        assert not out["trades"][0]["kpi"]["breach"]


class TestQuote:

    BOOK = [row("S1"), row("S2", gauge="G2", payer=False)]

    def _quote(self, new):
        return desk.quote(new, self.BOOK, {"CTPY-A": record("CTPY-A")}, STATE, hazard_for,
                          FAST, TODAY)

    def test_a_new_risk_consumes_capital(self):
        out = self._quote(row("NEW", gauge="G3", payer=False))
        assert out["netting_set_id"] == "NS-CTPY-A"
        assert out["incremental_kva"] < 0
        assert out["kva_spread_bps"] > 0          # a seller charges more for capital

    def test_a_hedge_releases_capital(self):
        """Selling on G1 offsets the book's G1 purchase: SA-CCR nets the two in
        one commodity type, so the quote carries a capital benefit."""
        out = self._quote(row("NEW", gauge="G1", payer=False))
        assert out["incremental_kva"] > 0
        assert out["kva_spread_bps"] < 0

    def test_first_trade_with_a_counterparty(self):
        out = desk.quote(row("NEW", cpty="CTPY-Z"), [], {}, STATE, hazard_for, FAST, TODAY)
        alone = desk.run_book([row("NEW", cpty="CTPY-Z")], {}, STATE, hazard_for, FAST, TODAY)
        assert out["incremental_xva"] == pytest.approx(alone["summary"]["xva_total"])

    def test_rejects_a_matured_trade(self):
        with pytest.raises(ValueError, match="matured"):
            desk.quote({**row("NEW"), "maturity": TODAY.isoformat()}, [], {}, STATE,
                       hazard_for, FAST, TODAY)

    def test_with_paths(self):
        assert desk.with_paths(FAST, None) is FAST
        assert desk.with_paths(FAST, "500").n_paths == 500
