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

"""Tests for generate_hazard_curve_history_file — part 1."""

import pytest

import database
from db_helpers import tmp_catchment
from port.src.historical_eod import generate_hazard_curve_history_file


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); the history generator reads EOD
    snapshots and persists the hazard-curve history document through ``database``."""
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


# ---------------------------------------------------------------------------
# generate_hazard_curve_history_file
# ---------------------------------------------------------------------------

class TestGenerateHazardCurveHistoryFile:

    def test_empty_dir_produces_no_file(self, tmp_path):
        generate_hazard_curve_history_file(database.active_catchment())
        assert database.get_hazard_curve_history(database.active_catchment()) is None

    def test_single_snapshot_creates_file(self, tmp_path):
        _write_snapshot("2026-01-02")
        generate_hazard_curve_history_file(database.active_catchment())
        assert database.get_hazard_curve_history(database.active_catchment()) is not None

    def test_output_has_metadata_and_history(self, tmp_path):
        _write_snapshot("2026-01-02")
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        assert "metadata" in data
        assert "history" in data

    def test_metadata_num_snapshots(self, tmp_path):
        for dt in ["2026-01-02", "2026-01-05", "2026-01-06"]:
            _write_snapshot(dt)
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        assert data["metadata"]["num_snapshots"] == 3

    def test_history_keyed_by_gauge(self, tmp_path):
        _write_snapshot("2026-01-02", gauge_id="GAUGE-042")
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        assert "GAUGE-042" in data["history"]

    def test_history_keyed_by_trigger(self, tmp_path):
        _write_snapshot("2026-01-02")
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        gauge_hist = data["history"]["GAUGE-001"]
        assert "alert" in gauge_hist
        assert "warning" in gauge_hist

    def test_history_entries_have_date(self, tmp_path):
        _write_snapshot("2026-01-02")
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        entry = data["history"]["GAUGE-001"]["alert"][0]
        assert entry["date"] == "2026-01-02"

    def test_history_entries_have_tenors(self, tmp_path):
        _write_snapshot("2026-01-02", rates={"1": 0.05, "2": 0.055, "3": 0.06})
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        entry = data["history"]["GAUGE-001"]["alert"][0]
        assert "1" in entry and "2" in entry and "3" in entry

    def test_multiple_gauges_in_metadata(self, tmp_path):
        # Two snapshots with different gauges
        snap1 = {
            "date": "2026-01-02",
            "market_state_snapshot": {"hazard_term_structure": {
                "GAUGE-001": {"alert": {"1": 0.05}},
                "GAUGE-002": {"alert": {"1": 0.04}},
            }},
            "positions": [],
        }
        database.save_eod_snapshot(database.active_catchment(), "2026-01-02", snap1)
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        assert set(data["metadata"]["gauges"]) == {"GAUGE-001", "GAUGE-002"}

    def test_multiple_snapshots_produce_multiple_entries(self, tmp_path):
        for dt in ["2026-01-02", "2026-01-05", "2026-01-06"]:
            _write_snapshot(dt)
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        alert_entries = data["history"]["GAUGE-001"]["alert"]
        assert len(alert_entries) == 3

    def test_metadata_has_generated_at(self, tmp_path):
        _write_snapshot("2026-01-02")
        generate_hazard_curve_history_file(database.active_catchment())
        data = database.get_hazard_curve_history(database.active_catchment())
        assert "generated_at" in data["metadata"]
