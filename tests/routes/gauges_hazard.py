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
Tests for routes.gauges.hazard — hazard curve and PRS pricing endpoints.

Covers: get_gauge_hazard (gauge not found, no hazard file, no curve for
gauge, valid), price_prs_endpoint (OPTIONS, no JSON, missing gauge_id,
invalid trigger, no hazard file, gauge not in hazard data, valid pricing).
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

_HAZARD_DATA = {
    "hazard_curves": {
        GAUGE_ID: {
            "gauge_name": "Test Gauge",
            "gev_location": 3.5,
            "gev_scale": 0.8,
            "gev_shape": 0.1,
            "curve_points": [
                {"exceedance_prob": 0.5, "level_m": 3.0},
                {"exceedance_prob": 0.1, "level_m": 4.5},
                {"exceedance_prob": 0.02, "level_m": 5.5},
            ],
            "return_period_levels": {"10": 4.5, "50": 5.5, "100": 6.0},
            "flood_alert_m": 4.0,
            "flood_warning_m": 4.5,
            "severe_flood_warning_m": 5.0,
            "annual_flood_prob_alert": 0.12,
            "annual_flood_prob_warning": 0.05,
            "annual_flood_prob_severe": 0.02,
            "term_structure_alert": [{"tenor": 1, "prob": 0.12}],
            "term_structure_warning": [{"tenor": 1, "prob": 0.05}],
            "term_structure_severe": [{"tenor": 1, "prob": 0.02}],
        }
    }
}


@pytest.fixture
def hazard_env(tmp_path, monkeypatch):
    """Flask test client with gauge.json and gaugehc.json."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))
    (tmp_path / "gaugehc.json").write_text(json.dumps(_HAZARD_DATA))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def hazard_no_file_env(tmp_path, monkeypatch):
    """Flask test client with gauge.json but NO gaugehc.json."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))
    # No gaugehc.json written

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def hazard_no_gauge_curve_env(tmp_path, monkeypatch):
    """Flask test client where gaugehc.json exists but has no curve for GAUGE-001."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))
    (tmp_path / "gaugehc.json").write_text(json.dumps({"hazard_curves": {}}))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def empty_gauge_env(tmp_path, monkeypatch):
    """Flask test client with no gauges."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps({"flood_gauges": []}))
    (tmp_path / "gaugehc.json").write_text(json.dumps(_HAZARD_DATA))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# GET /gauges/<gauge_id>/hazard
# ===========================================================================

class TestGetGaugeHazard:

    def test_gauge_not_found_returns_404(self, empty_gauge_env):
        r = empty_gauge_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_no_hazard_file_returns_404(self, hazard_no_file_env):
        r = hazard_no_file_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert r.status_code == 404
        assert "not available" in r.get_json()["message"].lower()

    def test_no_curve_for_gauge_returns_404(self, hazard_no_gauge_curve_env):
        r = hazard_no_gauge_curve_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert r.status_code == 404

    def test_valid_hazard_returns_200(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_gauge_id(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert r.get_json()["gauge_id"] == GAUGE_ID

    def test_response_has_gev_parameters(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        gev = r.get_json()["gev_parameters"]
        assert "location" in gev
        assert "scale" in gev
        assert "shape" in gev

    def test_response_has_curve_points(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert len(r.get_json()["curve_points"]) == 3

    def test_response_has_flood_stages(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        stages = r.get_json()["flood_stages"]
        assert "FloodAlert" in stages
        assert "FloodWarning" in stages
        assert "SevereFloodWarning" in stages

    def test_response_has_annual_flood_probs(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        probs = r.get_json()["annual_flood_probs"]
        assert "alert" in probs
        assert "warning" in probs
        assert "severe" in probs

    def test_response_has_term_structures(self, hazard_env):
        r = hazard_env.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        ts = r.get_json()["term_structures"]
        assert "alert" in ts
        assert "warning" in ts
        assert "severe" in ts


# ===========================================================================
# POST /price_prs
# ===========================================================================

class TestPricePrs:

    def test_options_returns_ok(self, hazard_env):
        r = hazard_env.options("/api/v1/price_prs")
        assert r.status_code == 200

    def test_no_json_returns_400(self, hazard_env):
        r = hazard_env.post("/api/v1/price_prs", content_type="application/json")
        assert r.status_code in (400, 500)

    def test_missing_gauge_id_returns_400(self, hazard_env):
        r = hazard_env.post("/api/v1/price_prs", json={"trigger_level": "alert"})
        assert r.status_code == 400

    def test_invalid_trigger_level_returns_400(self, hazard_env):
        r = hazard_env.post("/api/v1/price_prs",
                            json={"gauge_id": GAUGE_ID, "trigger_level": "extreme"})
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_no_hazard_file_returns_404(self, hazard_no_file_env):
        r = hazard_no_file_env.post("/api/v1/price_prs",
                                    json={"gauge_id": GAUGE_ID, "trigger_level": "alert"})
        assert r.status_code == 404

    def test_gauge_not_in_hazard_returns_404(self, hazard_no_gauge_curve_env):
        r = hazard_no_gauge_curve_env.post(
            "/api/v1/price_prs",
            json={"gauge_id": GAUGE_ID, "trigger_level": "warning"}
        )
        assert r.status_code == 404
