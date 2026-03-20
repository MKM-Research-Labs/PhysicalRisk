# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for EOD snapshot generation and history."""


class TestEodSnapshot:
    """Tests for EOD snapshot generation."""

    def _market_state(self):
        return {"risk_free_rate": 0.03, "gauge_adjustments": {}}

    def test_generate_snapshot(self, pnl_engine, sample_enriched_trades):
        snapshot = pnl_engine.generate_eod_snapshot(
            sample_enriched_trades, self._market_state(), "2026-02-24"
        )
        assert snapshot["eod_id"] == "EOD-20260224"
        assert snapshot["date"] == "2026-02-24"
        assert "portfolio_summary" in snapshot
        assert "positions" in snapshot
        assert snapshot["portfolio_summary"]["num_open_trades"] == 2

    def test_snapshot_persists(self, pnl_engine, sample_enriched_trades):
        pnl_engine.generate_eod_snapshot(
            sample_enriched_trades, self._market_state(), "2026-02-24"
        )
        snapshot = pnl_engine.get_eod_snapshot("2026-02-24")
        assert snapshot is not None
        assert snapshot["eod_id"] == "EOD-20260224"

    def test_eod_history(self, pnl_engine, sample_enriched_trades):
        ms = self._market_state()
        pnl_engine.generate_eod_snapshot(sample_enriched_trades, ms, "2026-02-20")
        pnl_engine.generate_eod_snapshot(sample_enriched_trades, ms, "2026-02-21")

        history = pnl_engine.get_eod_history()
        assert len(history) == 2
        assert history[0]["date"] == "2026-02-21"  # most recent first

    def test_pnl_series(self, pnl_engine, sample_enriched_trades):
        ms = self._market_state()
        pnl_engine.generate_eod_snapshot(sample_enriched_trades, ms, "2026-02-20")
        pnl_engine.generate_eod_snapshot(sample_enriched_trades, ms, "2026-02-21")

        series = pnl_engine.get_pnl_series()
        assert len(series) == 2
        assert series[0]["date"] == "2026-02-20"
        assert series[1]["date"] == "2026-02-21"

    def test_idempotent_snapshot(self, pnl_engine, sample_enriched_trades):
        ms = self._market_state()
        pnl_engine.generate_eod_snapshot(sample_enriched_trades, ms, "2026-02-24")
        pnl_engine.generate_eod_snapshot(sample_enriched_trades, ms, "2026-02-24")

        assert len(pnl_engine.get_eod_history()) == 1
