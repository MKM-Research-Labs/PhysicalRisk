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

"""Tests for core_storms.py coverage: storms.json branch (lines 77-80)
and sequence_type name fallback (line 97/110)."""

import json

from tests.routes.propertyts._helpers import (
    PROP_ID,
    make_prop_file,
)


STORM_ID = "STORM-cat-001"
SEQ_ID = "SEQ-cat-001"


def _make_client_with_storms_json(tmp_path, monkeypatch, *,
                                   storms_json=None,
                                   storm_sequences_json=None,
                                   flood_events=None):
    """Build a Flask test client with storms.json metadata (not storm_sequences)."""
    from config import config

    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir(exist_ok=True)

    # Property flood data
    prop_data = {
        "property_id": PROP_ID,
        "location": {"lat": 51.5, "lon": -0.12},
        "elevation_m": 3.0,
        "floor_level_m": 3.2,
        "nearest_gauges": [{"gauge_id": "GAUGE-001", "distance_m": 500}],
        "summary": {"storms_flooded": 1, "max_depth_m": 0.5},
        "flood_events": flood_events or [{
            "storm_id": STORM_ID,
            "flooded": True,
            "exceeded_severe": True,
            "flood_depth_m": 0.5,
            "damage_ratio": 0.1,
            "arrival_time_hrs": 5,
            "peak_time_hrs": 12,
            "travel_time_hrs": 5,
            "retention_factor": 0.9,
            "readings": [{"wse_m": 3.4, "depth_m": 0.2, "flooded": True}],
        }],
    }
    (pts_dir / f"{PROP_ID}.json").write_text(json.dumps(prop_data))

    if storms_json is not None:
        (tmp_path / "storms.json").write_text(json.dumps(storms_json))

    if storm_sequences_json is not None:
        (tmp_path / "storm_sequences.json").write_text(json.dumps(storm_sequences_json))

    # Gauge data for nearest gauge enrichment
    gauge_data = {"flood_gauges": [{"FloodGauge": {
        "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
        "SensorDetails": {"GaugeInformation": {
            "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GroundLevelMeters": 3.0,
        }},
        "FloodStage": {"UK": {
            "FloodAlert": 4.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.0,
        }},
    }}]}
    (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestStormsJsonBranch:
    """Cover lines 77-80: storm metadata loaded from storms.json 'storms' key."""

    def test_metadata_from_storms_json(self, tmp_path, monkeypatch):
        """When storms.json has a 'storms' key (not 'sequences'), metadata is loaded."""
        storms_json = {
            "storms": [{
                "storm_id": STORM_ID,
                "name": "Atlantic-42",
                "intensity_category": "severe",
                "effective_precipitation_mm": 120.0,
            }]
        }
        client = _make_client_with_storms_json(
            tmp_path, monkeypatch,
            storms_json=storms_json,
        )

        resp = client.get(f"/api/v1/properties/{PROP_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()

        events = data["flood_events"]
        assert len(events) >= 1
        event = events[0]
        assert event["name"] == "Atlantic-42"
        assert event["intensity_category"] == "severe"
        assert event["effective_precipitation_mm"] == 120.0


class TestNameFallbackFromCategory:
    """Cover line 110: name fallback uses intensity_category.capitalize()."""

    def test_name_defaults_to_capitalized_category(self, tmp_path, monkeypatch):
        """When storms.json has no 'name' but has intensity_category,
        the name defaults to the capitalized category."""
        storms_json = {
            "storms": [{
                "storm_id": STORM_ID,
                "intensity_category": "moderate",
                # no 'name' field
            }]
        }
        client = _make_client_with_storms_json(
            tmp_path, monkeypatch,
            storms_json=storms_json,
        )

        resp = client.get(f"/api/v1/properties/{PROP_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()

        events = data["flood_events"]
        assert len(events) >= 1
        event = events[0]
        # name should default to capitalized intensity_category
        assert event["name"] == "Moderate"

    def test_name_defaults_empty_when_no_category(self, tmp_path, monkeypatch):
        """When storms.json has neither 'name' nor 'intensity_category',
        the name defaults to empty string."""
        storms_json = {
            "storms": [{
                "storm_id": STORM_ID,
                # no 'name', no 'intensity_category'
            }]
        }
        client = _make_client_with_storms_json(
            tmp_path, monkeypatch,
            storms_json=storms_json,
        )

        resp = client.get(f"/api/v1/properties/{PROP_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()

        events = data["flood_events"]
        assert len(events) >= 1
        event = events[0]
        assert event["name"] == ""
