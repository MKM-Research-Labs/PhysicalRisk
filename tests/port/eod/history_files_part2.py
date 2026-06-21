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

"""Tests for generate_trade_pnl_history_file — part 2."""

import pytest

import database
from db_helpers import tmp_catchment
from port.src.historical_eod import generate_trade_pnl_history_file


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); the history generator reads EOD
    snapshots and persists the trade-P&L history document through ``database``."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_snapshot(date_str, gauge_id="GAUGE-001", rates=None, positions=None):
    """Seed a minimal EOD snapshot via the database."""
    rates = rates or {"1": 0.05, "2": 0.055, "3": 0.06}
    snap = {
        "date": date_str,
        "market_state_snapshot": {
            "hazard_term_structure": {
                gauge_id: {
                    "alert": rates,
                    "warning": {k: v * 0.6 for k, v in rates.items()},
                }
            }
        },
        "positions": positions or [],
    }
    database.save_eod_snapshot(database.active_catchment(), date_str, snap)
    return snap


def _make_pos(swap_id, fair=210.0, mkt=500.0, running=5000.0, gauge="GAUGE-001"):
    return {
        "swap_id": swap_id,
        "trade_date": "2026-01-02",
        "trade_spread_bps": 200.0,
        "gauge_id": gauge,
        "trigger": "alert",
        "notional": 1_000_000,
        "is_payer": True,
        "fair_spread_bps": fair,
        "market_pnl": mkt,
        "running_pnl": running,
    }


# ---------------------------------------------------------------------------
# generate_trade_pnl_history_file
# ---------------------------------------------------------------------------

class TestGenerateTradePnlHistoryFile:

    def test_empty_dir_produces_no_file(self, tmp_path):
        generate_trade_pnl_history_file(database.active_catchment())
        assert database.get_trade_pnl_history(database.active_catchment()) is None

    def test_single_snapshot_creates_file(self, tmp_path):
        _write_snapshot("2026-01-02", positions=[_make_pos("PRS-001")])
        generate_trade_pnl_history_file(database.active_catchment())
        assert database.get_trade_pnl_history(database.active_catchment()) is not None

    def test_output_has_metadata_and_trades(self, tmp_path):
        _write_snapshot("2026-01-02", positions=[_make_pos("PRS-001")])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert "metadata" in data
        assert "trades" in data

    def test_trade_keyed_by_swap_id(self, tmp_path):
        _write_snapshot("2026-01-02", positions=[_make_pos("PRS-001")])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert "PRS-001" in data["trades"]

    def test_trade_metadata_fields(self, tmp_path):
        _write_snapshot("2026-01-02", positions=[_make_pos("PRS-001")])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        t = data["trades"]["PRS-001"]
        assert "gauge_id" in t
        assert "trigger" in t
        assert "notional" in t
        assert "is_payer" in t
        assert "history" in t

    def test_history_entry_structure(self, tmp_path):
        _write_snapshot("2026-01-02", positions=[_make_pos("PRS-001", fair=215.0, mkt=600.0, running=1200.0)])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        entry = data["trades"]["PRS-001"]["history"][0]
        assert entry["date"] == "2026-01-02"
        assert entry["mark"] == 215.0
        assert entry["mkt_pnl"] == 600.0
        assert entry["running_pnl"] == 1200.0

    def test_multiple_days_builds_history_vector(self, tmp_path):
        for i, dt in enumerate(["2026-01-02", "2026-01-05", "2026-01-06"]):
            _write_snapshot(dt, positions=[_make_pos("PRS-001", fair=210.0 + i)])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert len(data["trades"]["PRS-001"]["history"]) == 3

    def test_multiple_trades_in_snapshot(self, tmp_path):
        positions = [_make_pos("PRS-001"), _make_pos("PRS-002"), _make_pos("PRS-003")]
        _write_snapshot("2026-01-02", positions=positions)
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert data["metadata"]["num_trades"] == 3

    def test_position_missing_swap_id_is_skipped(self, tmp_path):
        positions = [_make_pos("PRS-001"), {"gauge_id": "GAUGE-001"}]  # second has no swap_id
        _write_snapshot("2026-01-02", positions=positions)
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert "PRS-001" in data["trades"]
        assert len(data["trades"]) == 1

    def test_metadata_num_snapshots(self, tmp_path):
        for dt in ["2026-01-02", "2026-01-05", "2026-01-06"]:
            _write_snapshot(dt, positions=[_make_pos("PRS-001")])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert data["metadata"]["num_snapshots"] == 3

    def test_metadata_has_generated_at(self, tmp_path):
        _write_snapshot("2026-01-02", positions=[_make_pos("PRS-001")])
        generate_trade_pnl_history_file(database.active_catchment())
        data = database.get_trade_pnl_history(database.active_catchment())
        assert "generated_at" in data["metadata"]
