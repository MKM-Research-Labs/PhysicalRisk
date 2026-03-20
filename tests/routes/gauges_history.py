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

"""
Tests for routes.gauges.history — gauge history, timeseries, and statistics.

Covers: get_gauge_history (no file→404, valid→200, days param, statistics/metadata),
get_gaugets (gauge not found→404, valid→200), get_gauge_statistics (not found→404, valid→200).
"""

import json
from pathlib import Path

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

GAUGE_ID = "GAUGE-001"

_GAUGE_DATA = {
    "flood_gauges": [{
        "FloodGauge": {
            "Header": {"GaugeID": GAUGE_ID, "GaugeName": "Test Gauge"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStage": {"UK": {
                "FloodAlert": 4.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.0
            }},
            "SensorDetails": {"GaugeInformation": {
                "GaugeType": "Pressure", "GaugeOwner": "EA",
                "OperationalStatus": "Active",
                "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GaugeDatum": 0.0,
            }, "SensorSpecifications": {}, "Measurements": {}},
            "SensorStats": {"HistoricalHighLevel": 6.0, "HistoricalHighDate": "2024-01-01"},
            "NRFAMetadata": {},
        }
    }]
}

_HD_DATA = {
    "gauge_metadata": {
        "gauge_id": GAUGE_ID,
        "gauge_name": "Test Gauge",
        "flood_stages": {"alert": 4.0, "warning": 4.5, "severe": 5.0},
    },
    "statistics": {
        "mean_level": 2.5,
        "max_level": 5.8,
        "min_level": 0.5,
        "flood_days_above_alert": 12,
    },
    "daily_observations": [
        {"date": f"2024-{m:02d}-01", "level_meters": 2.0 + m * 0.1}
        for m in range(1, 13)
    ],
}


@pytest.fixture
def history_env(tmp_path, monkeypatch):
    """Flask test client with gauge.json and gaugehd file."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))

    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()
    (gaugehd_dir / f"gauge_{GAUGE_ID}_hd.json").write_text(json.dumps(_HD_DATA))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    # Write minimal gauge timeseries
    gaugets_data = {
        "gauge_id": GAUGE_ID,
        "flood_simulation": {"readings": [{"waterLevel": 3.0}] * 10},
    }
    (gaugets_dir / f"{GAUGE_ID}.json").write_text(json.dumps(gaugets_data))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def history_no_hd_env(tmp_path, monkeypatch):
    """Flask test client with gauge.json but NO gaugehd file."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))

    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()  # directory exists but no files

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def empty_gauge_env(tmp_path, monkeypatch):
    """Flask test client with empty gauge list."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps({"flood_gauges": []}))
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()
    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# GET /gauges/<gauge_id>/history
# ===========================================================================

class TestGetGaugeHistory:

    def test_no_history_file_returns_404(self, history_no_hd_env):
        r = history_no_hd_env.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_history_returns_200(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_daily_observations(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        data = r.get_json()
        assert "daily_observations" in data
        assert len(data["daily_observations"]) == 12

    def test_response_has_statistics(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        data = r.get_json()
        assert "statistics" in data
        assert data["statistics"]["mean_level"] == 2.5

    def test_response_has_gauge_metadata(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        data = r.get_json()
        assert "gauge_metadata" in data

    def test_response_has_flood_stages(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        data = r.get_json()
        assert "flood_stages" in data

    def test_days_param_limits_observations(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history?days=5")
        data = r.get_json()
        assert len(data["daily_observations"]) == 5

    def test_days_param_zero_returns_all(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history?days=0")
        data = r.get_json()
        # days=0 → doesn't filter (0 is falsy)
        assert len(data["daily_observations"]) == 12

    def test_days_larger_than_available_returns_all(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/history?days=100")
        data = r.get_json()
        assert len(data["daily_observations"]) == 12


# ===========================================================================
# GET /gauges/<gauge_id>/timeseries
# ===========================================================================

class TestGetGaugets:

    def test_gauge_not_found_returns_404(self, empty_gauge_env):
        r = empty_gauge_env.get(f"/api/v1/gauges/GAUGE-GHOST/timeseries")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_gauge_returns_success(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/timeseries")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["gauge_id"] == GAUGE_ID

    def test_response_has_count_and_readings(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/timeseries")
        data = r.get_json()
        assert "count" in data
        assert "readings" in data
        assert isinstance(data["count"], int)


# ===========================================================================
# GET /gauges/<gauge_id>/statistics
# ===========================================================================

class TestGetGaugeStatistics:

    def test_gauge_not_found_returns_404(self, empty_gauge_env):
        r = empty_gauge_env.get(f"/api/v1/gauges/GAUGE-GHOST/statistics")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_gauge_returns_success(self, history_env):
        r = history_env.get(f"/api/v1/gauges/{GAUGE_ID}/statistics")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert "statistics" in data


# ===========================================================================
# GET /gauges/history/summary  (startup preloader stat)
# ===========================================================================

class TestGaugeHistorySummary:

    def test_returns_200_with_no_gaugehd_files(self, history_no_hd_env):
        r = history_no_hd_env.get("/api/v1/gauges/history/summary")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] == 0

    def test_returns_correct_count_when_files_present(self, history_env):
        r = history_env.get("/api/v1/gauges/history/summary")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] == 1
        assert data["gauges"] == 1

    def test_response_has_count_and_gauges_keys(self, history_env):
        data = history_env.get("/api/v1/gauges/history/summary").get_json()
        assert "count" in data
        assert "gauges" in data
        assert isinstance(data["count"], int)
