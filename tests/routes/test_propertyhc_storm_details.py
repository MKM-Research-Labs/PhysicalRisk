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

"""
Tests for storm_details and gauge_thresholds in property hazard API response.

Covers:
  GET /api/v1/properties/<id>/hazard — storm_details array passthrough
"""

import json

import pytest

from config import config


SAMPLE_WITH_STORM_DETAILS = {
    "metadata": {
        "generated_at": "2026-01-01T00:00:00",
        "catchment": "thames",
        "num_properties": 1,
    },
    "summary": {
        "total_properties": 1,
        "avg_flood_count": 3.0,
    },
    "property_hazard_curves": {
        "PROP-SD01": {
            "property_id": "PROP-SD01",
            "flood_count": 3,
            "elevation_m": 5.0,
            "floor_level_m": 0.3,
            "summary": {
                "avg_basis_bps": 4.0,
                "flood_transmission_rate": 0.06,
                "max_depth_m": 0.5,
            },
            "nearest_gauges": [
                {
                    "gauge_id": "GAUGE-001",
                    "distance_km": 1.5,
                    "gauge_elevation_m": 3.5,
                    "event_basis": 5,
                    "flood_transmission_rate": 0.06,
                    "gauge_thresholds": {
                        "alert_level": 3.5,
                        "warning_level": 4.5,
                        "severe_level": 5.0,
                    },
                }
            ],
            "storm_details": [
                {
                    "storm_id": "S1",
                    "gauge_peak_m": 5.5,
                    "flood_depth_m": 0.3,
                    "damage_ratio": 0.1,
                    "flooded": True,
                    "exceeded_severe": True,
                    "retention_factor": 0.85,
                },
                {
                    "storm_id": "S2",
                    "gauge_peak_m": 4.8,
                    "flood_depth_m": 0.0,
                    "damage_ratio": 0.0,
                    "flooded": False,
                    "exceeded_severe": False,
                    "retention_factor": 0.85,
                },
                {
                    "storm_id": "S3",
                    "gauge_peak_m": 6.0,
                    "flood_depth_m": 0.5,
                    "damage_ratio": 0.25,
                    "flooded": True,
                    "exceeded_severe": True,
                    "retention_factor": 0.85,
                },
            ],
        },
    },
}


@pytest.fixture
def sd_client(tmp_path, monkeypatch):
    """Client with propertyhc.json containing storm_details."""
    (tmp_path / "propertyhc.json").write_text(
        json.dumps(SAMPLE_WITH_STORM_DETAILS)
    )
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# storm_details in GET /api/v1/properties/<id>/hazard
# ===========================================================================

class TestStormDetailsInHazardResponse:

    def test_storm_details_present(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert "storm_details" in data

    def test_storm_details_count(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        storms = r.get_json()["data"]["storm_details"]
        assert len(storms) == 3

    def test_storm_details_fields(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        storm = r.get_json()["data"]["storm_details"][0]
        assert "storm_id" in storm
        assert "gauge_peak_m" in storm
        assert "flood_depth_m" in storm
        assert "damage_ratio" in storm
        assert "flooded" in storm
        assert "exceeded_severe" in storm
        assert "retention_factor" in storm

    def test_storm_details_values(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        storm = r.get_json()["data"]["storm_details"][0]
        assert storm["storm_id"] == "S1"
        assert storm["gauge_peak_m"] == 5.5
        assert storm["flooded"] is True

    def test_non_flooded_storm_in_details(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        storms = r.get_json()["data"]["storm_details"]
        non_flooded = [s for s in storms if not s["flooded"]]
        assert len(non_flooded) == 1
        assert non_flooded[0]["storm_id"] == "S2"
        assert non_flooded[0]["flood_depth_m"] == 0.0


# ===========================================================================
# gauge_thresholds in GET /api/v1/properties/<id>/hazard
# ===========================================================================

class TestGaugeThresholdsInHazardResponse:

    def test_gauge_thresholds_present(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        ng = r.get_json()["data"]["nearest_gauges"][0]
        assert "gauge_thresholds" in ng

    def test_gauge_thresholds_alert_level(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        thresholds = r.get_json()["data"]["nearest_gauges"][0]["gauge_thresholds"]
        assert thresholds["alert_level"] == 3.5

    def test_gauge_thresholds_warning_level(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        thresholds = r.get_json()["data"]["nearest_gauges"][0]["gauge_thresholds"]
        assert thresholds["warning_level"] == 4.5

    def test_gauge_thresholds_severe_level(self, sd_client):
        r = sd_client.get("/api/v1/properties/PROP-SD01/hazard")
        thresholds = r.get_json()["data"]["nearest_gauges"][0]["gauge_thresholds"]
        assert thresholds["severe_level"] == 5.0
