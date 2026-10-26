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

"""The delta engine's MTM and floor behaviour, after the MKM-DE-001 Wolfram benchmark.

Two defects the benchmark found: MTM was valued with the risky annuity after it
had been rounded to 6 dp for display, and a position whose fair spread sits on
the 2 bp floor reported almost no FS01 without saying why. MTM now uses the
unrounded annuity, and the delta carries ``at_floor`` and the hazard sensitivity
of the unfloored spread beside the (correctly near-zero) P&L sensitivity.
"""

import pytest

from models.trading.delta_engine.engine import DeltaEngine
from models.trading.delta_engine.pricer import (
    compute_gauge_delta,
    compute_mark_to_market,
    compute_prs_spread,
    compute_risky_annuity,
)

from .test_engine_coverage import _base_trade, _iso_catchment, _make_gaugehc  # noqa: F401


class TestFloor:
    def test_on_the_floor_the_hazard_sensitivity_is_reported(self):
        d = compute_gauge_delta(0.0001, 5, 10_000_000)
        assert d["at_floor"] is True
        assert d["delta_spread_bps"] < 0.1
        assert d["hazard_delta_bps"] == pytest.approx(1.0, abs=0.01)

    def test_off_the_floor_both_sensitivities_agree(self):
        d = compute_gauge_delta(0.02, 5, 10_000_000)
        assert d["at_floor"] is False
        assert d["hazard_delta_bps"] == d["delta_spread_bps"]


class TestMtm:
    def test_enrich_trade_values_mtm_with_the_unrounded_annuity(self):
        from models.trading.market_state import MarketStateManager

        _make_gaugehc()
        mgr = MarketStateManager()
        state = mgr.load()
        enriched = DeltaEngine(mgr).enrich_trade(_base_trade(), state)
        rate, tenor = enriched["current_hazard_rate"], max(enriched["tenor"], 1)
        rf, curve = state.get("risk_free_rate", 0.03), state.get("yield_curve")
        annuity = compute_risky_annuity(rate, tenor, rf, curve)
        fair = compute_prs_spread(rate, tenor, 0.0, rf, yield_curve=curve)
        assert enriched["mtm"] == compute_mark_to_market(250.0, fair, annuity, 10_000_000)
        assert enriched["risky_annuity"] == round(annuity, 6)
        assert "gauge_at_floor" in enriched and "gauge_hazard_delta_bps" in enriched
