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
Tests for routes.gauges.reports — /gauges/report endpoint.

Covers: OPTIONS, missing JSON, missing gauge ID, gauge not found,
and the happy-path report generation.
"""

import json
from pathlib import Path

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def gauge_env(tmp_path, monkeypatch):
    """Flask test client with a minimal gauge file for report generation."""
    from config import config

    gauge_id = "GAUGE-001"

    # Write gauge.json
    gauge_data = {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {
                        "GaugeID": gauge_id,
                        "GaugeName": "Test Gauge",
                        "createdDate": "2024-01-01",
                        "lastModifiedDate": "2024-12-01",
                    },
                    "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                    "FloodStage": {
                        "UK": {
                            "FloodAlert": 4.5,
                            "FloodWarning": 5.5,
                            "SevereFloodWarning": 6.5,
                        }
                    },
                    "SensorDetails": {
                        "GaugeInformation": {
                            "GaugeType": "Pressure",
                            "GaugeOwner": "EA",
                            "OperationalStatus": "Active",
                            "GaugeLatitude": 51.5,
                            "GaugeLongitude": -0.1,
                            "GaugeDatum": 0.0,
                        },
                        "SensorSpecifications": {},
                        "Measurements": {},
                    },
                    "SensorStats": {
                        "HistoricalHighLevel": 6.85,
                        "HistoricalHighDate": "2024-01-15",
                    },
                    "NRFAMetadata": {},
                }
            }
        ]
    }
    (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

    reports_dir = tmp_path / "reports" / "gauges"
    reports_dir.mkdir(parents=True)

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()

    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: reports_dir)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), gauge_id


@pytest.fixture
def gauge_client_empty(tmp_path, monkeypatch):
    """Flask test client with no gauges (empty gauge.json)."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps({"flood_gauges": []}))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path / "gaugehd")
    monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: tmp_path / "reports")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# Tests
# ===========================================================================

class TestGenerateGaugeReport:

    def test_options_returns_ok(self, gauge_client_empty):
        r = gauge_client_empty.options("/api/v1/gauges/report")
        assert r.status_code == 200

    def test_no_json_returns_400(self, gauge_client_empty):
        r = gauge_client_empty.post(
            "/api/v1/gauges/report",
            content_type="application/json",
        )
        assert r.status_code in (400, 415, 500)

    def test_missing_gauge_id_returns_400(self, gauge_client_empty):
        r = gauge_client_empty.post(
            "/api/v1/gauges/report",
            json={},
        )
        assert r.status_code == 400
        data = r.get_json()
        assert data["status"] == "error"

    def test_gauge_not_found_returns_404(self, gauge_client_empty):
        r = gauge_client_empty.post(
            "/api/v1/gauges/report",
            json={"gaugeId": "GAUGE-NONEXISTENT"},
        )
        assert r.status_code == 404
        data = r.get_json()
        assert data["status"] == "error"

    def test_valid_gauge_generates_report(self, gauge_env):
        client, gauge_id = gauge_env
        r = client.post(
            "/api/v1/gauges/report",
            json={"gaugeId": gauge_id},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"

    def test_response_has_pdf_base64(self, gauge_env):
        client, gauge_id = gauge_env
        r = client.post("/api/v1/gauges/report", json={"gaugeId": gauge_id})
        data = r.get_json()
        assert "pdf_base64" in data
        assert len(data["pdf_base64"]) > 0

    def test_response_has_file_path(self, gauge_env):
        client, gauge_id = gauge_env
        r = client.post("/api/v1/gauges/report", json={"gaugeId": gauge_id})
        data = r.get_json()
        assert "file_path" in data
        assert data["file_path"].endswith(".pdf")

    def test_legacy_route_alias(self, gauge_env):
        """The /generate_gauge_report alias also works."""
        client, gauge_id = gauge_env
        r = client.post("/api/v1/generate_gauge_report", json={"gaugeId": gauge_id})
        assert r.status_code == 200

    def test_null_json_body_returns_400(self, gauge_client_empty):
        """Sending JSON null body makes get_json() return None → line 29."""
        r = gauge_client_empty.post(
            "/api/v1/gauges/report",
            data=b"null",
            content_type="application/json",
        )
        assert r.status_code == 400

    def test_with_gaugehd_file_present(self, tmp_path, monkeypatch):
        """gaugehd file exists → exercises lines 62-69."""
        from config import config
        import json as j

        gauge_id = "GAUGE-001"
        gauge_data = {"flood_gauges": [{"FloodGauge": {
            "Header": {"GaugeID": gauge_id, "GaugeName": "T"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStage": {"UK": {"FloodAlert": 4.5, "FloodWarning": 5.5, "SevereFloodWarning": 6.5}},
            "SensorDetails": {"GaugeInformation": {"GaugeType": "P", "GaugeOwner": "EA", "OperationalStatus": "A", "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GaugeDatum": 0.0}, "SensorSpecifications": {}, "Measurements": {}},
            "SensorStats": {"HistoricalHighLevel": 6.0, "HistoricalHighDate": "2024-01-01"},
            "NRFAMetadata": {},
        }}]}
        (tmp_path / "gauge.json").write_text(j.dumps(gauge_data))

        # Create gaugehd file for this gauge
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        hd_data = {"daily_observations": [{"date": "2024-01-01", "level_meters": 3.0}]}
        (gaugehd_dir / f"gauge_{gauge_id}_hd.json").write_text(j.dumps(hd_data))

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: reports_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post("/api/v1/gauges/report", json={"gaugeId": gauge_id})
        assert r.status_code == 200

    def test_with_hazard_file_present(self, tmp_path, monkeypatch):
        """gaugehc.json exists → exercises lines 76-82."""
        from config import config
        import json as j

        gauge_id = "GAUGE-001"
        gauge_data = {"flood_gauges": [{"FloodGauge": {
            "Header": {"GaugeID": gauge_id, "GaugeName": "T"},
            "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
            "FloodStage": {"UK": {"FloodAlert": 4.5, "FloodWarning": 5.5, "SevereFloodWarning": 6.5}},
            "SensorDetails": {"GaugeInformation": {"GaugeType": "P", "GaugeOwner": "EA", "OperationalStatus": "A", "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GaugeDatum": 0.0}, "SensorSpecifications": {}, "Measurements": {}},
            "SensorStats": {"HistoricalHighLevel": 6.0, "HistoricalHighDate": "2024-01-01"},
            "NRFAMetadata": {},
        }}]}
        (tmp_path / "gauge.json").write_text(j.dumps(gauge_data))

        # Create hazard file
        hc_data = {"hazard_curves": {gauge_id: {"exceedance": [0.1, 0.05], "levels": [4.5, 5.5]}}}
        (tmp_path / "gaugehc.json").write_text(j.dumps(hc_data))

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: tmp_path / "gaugehd")
        monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: reports_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post("/api/v1/gauges/report", json={"gaugeId": gauge_id})
        assert r.status_code == 200
