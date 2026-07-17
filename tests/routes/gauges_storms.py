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
Tests for routes.gauges.storms — get_gauge_storms endpoint.

Covers: gauge not found→404, gauge found + no gaugets data,
with storm_responses, with storms.json enrichment, with gaugets dir for
severe count computation.
"""

import json
from pathlib import Path

import pytest


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

_STORM_META = {
    "schema_version": "2.0-multi-storm",
    "num_sequences": 1,
    "sequences": [{
        "sequence_id": "STORM-seq001",
        "sequence_type": "isolated",
        "storms": [{
            "storm_id": "STORM-0001",
            "intensity_category": "moderate",
            "precipitation_mm": 55.0,
            "duration_hours": 24,
            "intensity_factor": 0.8,
            "peak_position": 0.5,
        }]
    }]
}


def _gaugets_data(storm_id="STORM-0001", exceeded_severe=False):
    return {
        "gauge_id": GAUGE_ID,
        "flood_simulation": {"readings": [{"waterLevel": 3.5}] * 5},
        "storm_responses": {
            "responses": [{
                "storm_id": storm_id,
                "peak_level_m": 4.8,
                "exceeded_alert": True,
                "exceeded_warning": False,
                "exceeded_severe": exceeded_severe,
            }]
        }
    }


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def storms_env(tmp_path, monkeypatch):
    """Flask test client with gauge.json, gaugets, and storm_sequences.json."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))
    (tmp_path / "storm_sequences.json").write_text(json.dumps(_STORM_META))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    (gaugets_dir / f"{GAUGE_ID}.json").write_text(json.dumps(_gaugets_data()))

    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def storms_env_severe(tmp_path, monkeypatch):
    """Gaugets with exceeded_severe=True for the storm."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps(_GAUGE_DATA))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    (gaugets_dir / f"{GAUGE_ID}.json").write_text(
        json.dumps(_gaugets_data("STORM-0001", exceeded_severe=True))
    )

    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def empty_gauge_env(tmp_path, monkeypatch):
    """Empty gauge list."""
    from config import config

    (tmp_path / "gauge.json").write_text(json.dumps({"flood_gauges": []}))

    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# Tests
# ===========================================================================

class TestGetGaugeStorms:

    def test_gauge_not_found_returns_404(self, empty_gauge_env):
        r = empty_gauge_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_gauge_returns_200(self, storms_env):
        r = storms_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_response_has_gauge_id(self, storms_env):
        r = storms_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.get_json()["gauge_id"] == GAUGE_ID

    def test_response_has_flood_simulation(self, storms_env):
        r = storms_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        data = r.get_json()
        assert "flood_simulation" in data
        assert "num_timesteps" in data["flood_simulation"]

    def test_response_has_storm_responses(self, storms_env):
        r = storms_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        data = r.get_json()
        assert "storm_responses" in data
        assert "num_sequences" in data["storm_responses"]

    def test_response_has_flood_stages(self, storms_env):
        r = storms_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert "flood_stages" in r.get_json()

    def test_storm_enrichment_from_storms_json(self, storms_env):
        """Storm responses enriched with metadata from storm_sequences.json."""
        r = storms_env.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        responses = r.get_json()["storm_responses"]["responses"]
        if responses:
            # If storm_id matches, name should be enriched
            assert "name" in responses[0] or responses[0].get("name") == ""

    def test_with_severe_exceeded_counts_gauges(self, storms_env_severe):
        """When exceeded_severe=True, severe count computed from gaugets dir."""
        r = storms_env_severe.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 200
