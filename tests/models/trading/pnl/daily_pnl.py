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

"""Tests for daily P&L computation and phantom P&L fix."""

from datetime import date


class TestDailyPnL:
    """Tests for daily P&L computation."""

    def test_daily_pnl_without_previous_eod(self, pnl_engine, sample_enriched_trades):
        result = pnl_engine.compute_daily_pnl(sample_enriched_trades)
        assert result["num_open_trades"] == 2
        assert result["total_notional"] == 15_000_000
        assert len(result["positions"]) == 2

    def test_running_pnl_calculation(self, pnl_engine, sample_enriched_trades):
        result = pnl_engine.compute_daily_pnl(sample_enriched_trades)

        pos1 = next(p for p in result["positions"] if p["swap_id"] == "PRS-001")
        assert abs(pos1["running_pnl"] - 43_500) < 1

        pos2 = next(p for p in result["positions"] if p["swap_id"] == "PRS-002")
        assert abs(pos2["running_pnl"] - (-7_125)) < 1

    def test_pnl_decomposition_sums(self, pnl_engine, sample_enriched_trades):
        result = pnl_engine.compute_daily_pnl(sample_enriched_trades)
        for pos in result["positions"]:
            assert abs(pos["daily_pnl"] - (pos["new_trade_pnl"] + pos["market_pnl"])) < 0.01

    def test_closed_trades_excluded(self, pnl_engine):
        trades = [{
            "swap_id": "PRS-CLOSED",
            "gauge_id": "G1",
            "notional": 10_000_000,
            "trade_spread_bps": 100,
            "fair_spread_bps": 120,
            "is_payer": True,
            "risky_annuity": 4.0,
            "trade_status": "Closed",
            "trade_date": "2026-01-01",
            "gauge_fs01": 0,
            "basis_dv01": 0,
        }]
        assert pnl_engine.compute_daily_pnl(trades)["num_open_trades"] == 0


class TestPhantomPnLFix:
    """Tests for the phantom P&L fix — trades not in previous EOD."""

    def test_market_pnl_zero_for_missing_eod_trade(self, pnl_engine):
        trades = [{
            "swap_id": "PRS-ORPHAN",
            "gauge_id": "GAUGE-X",
            "notional": 10_000_000,
            "trade_spread_bps": 200.0,
            "fair_spread_bps": 250.0,
            "is_payer": True,
            "risky_annuity": 4.0,
            "trade_status": "Open",
            "trade_date": "2026-01-01",
            "gauge_fs01": 3000,
            "basis_dv01": 0,
        }]
        result = pnl_engine.compute_daily_pnl(trades, previous_eod={"positions": []})
        pos = result["positions"][0]
        assert abs(pos["market_pnl"]) < 0.01
        assert abs(pos["new_trade_pnl"]) < 0.01
        assert abs(pos["daily_pnl"]) < 0.01

    def test_market_pnl_nonzero_with_eod_mark(self, pnl_engine):
        trades = [{
            "swap_id": "PRS-MARKED",
            "gauge_id": "GAUGE-X",
            "notional": 10_000_000,
            "trade_spread_bps": 200.0,
            "fair_spread_bps": 260.0,
            "is_payer": True,
            "risky_annuity": 4.0,
            "trade_status": "Open",
            "trade_date": "2026-01-01",
            "gauge_fs01": 3000,
            "basis_dv01": 0,
        }]
        prev_eod = {"positions": [{"swap_id": "PRS-MARKED", "fair_spread_bps": 240.0,
                                   "running_pnl": 160_000.0}]}
        result = pnl_engine.compute_daily_pnl(trades, previous_eod=prev_eod)
        assert abs(result["positions"][0]["market_pnl"] - 80_000.0) < 1

    def test_new_trade_has_inception_pnl(self, pnl_engine):
        today_str = date.today().isoformat()
        trades = [{
            "swap_id": "PRS-NEW",
            "gauge_id": "GAUGE-X",
            "notional": 5_000_000,
            "trade_spread_bps": 180.0,
            "fair_spread_bps": 200.0,
            "is_payer": True,
            "risky_annuity": 3.0,
            "trade_status": "Open",
            "trade_date": today_str,
            "gauge_fs01": 2000,
            "basis_dv01": 0,
        }]
        result = pnl_engine.compute_daily_pnl(trades)
        pos = result["positions"][0]
        expected = (200.0 - 180.0) / 10000 * 3.0 * 5_000_000
        assert abs(pos["new_trade_pnl"] - expected) < 1
        assert abs(pos["market_pnl"]) < 0.01

    def test_pnl_decomposition_with_prev_eod(self, pnl_engine):
        today_str = date.today().isoformat()
        trades = [
            {
                "swap_id": "PRS-A",
                "gauge_id": "G1",
                "notional": 10_000_000,
                "trade_spread_bps": 200.0,
                "fair_spread_bps": 220.0,
                "is_payer": True,
                "risky_annuity": 4.0,
                "trade_status": "Open",
                "trade_date": "2026-01-01",
                "gauge_fs01": 3000,
                "basis_dv01": 0,
            },
            {
                "swap_id": "PRS-B",
                "gauge_id": "G1",
                "notional": 5_000_000,
                "trade_spread_bps": 150.0,
                "fair_spread_bps": 160.0,
                "is_payer": False,
                "risky_annuity": 3.0,
                "trade_status": "Open",
                "trade_date": today_str,
                "gauge_fs01": -1500,
                "basis_dv01": 0,
            },
        ]
        prev_eod = {"positions": [{"swap_id": "PRS-A", "fair_spread_bps": 210.0}]}
        result = pnl_engine.compute_daily_pnl(trades, previous_eod=prev_eod)
        for pos in result["positions"]:
            assert abs(pos["daily_pnl"] - (pos["new_trade_pnl"] + pos["market_pnl"])) < 0.01
