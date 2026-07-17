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

"""Tests for routes/propertyts/core.py — storm listing and missing-file edge cases. (part 2 of 2)"""

import json

import pytest


# ===========================================================================
# Coverage expansion — missing lines 134-135, 157-158
# ===========================================================================

class TestStormListExceptionHandlers:
    """Lines 63, 75: exception/edge cases in stress_storms parsing."""

    def test_storm_with_empty_id_is_skipped(self, tmp_path, monkeypatch):
        """Line 63: storm with empty storm_id → continue (skipped)."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        # stress_storms/_index.json with one valid and one empty-id storm
        ss_dir = tmp_path / "stress_storms"
        ss_dir.mkdir()
        ss_index = {
            "storms": [
                {"storm_id": "", "name": "Empty", "intensity_category": "moderate",
                 "trigger_summary": {"gauges_severe": 1}},
                {"storm_id": "STORM-VALID", "name": "Valid", "intensity_category": "severe",
                 "effective_precipitation_mm": 80,
                 "trigger_summary": {"gauges_severe": 3}},
            ],
        }
        (ss_dir / "_index.json").write_text(json.dumps(ss_index))

        # Property with flooding for the valid storm
        prop_data = {
            "property_id": "PROP-001",
            "flood_events": [{"storm_id": "STORM-VALID", "flood_depth_m": 0.5, "damage_ratio": 0.1}],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))
        prop_val = {"properties": [{"PropertyHeader": {"Header": {"PropertyID": "PROP-001"}}}]}
        (tmp_path / "property.json").write_text(json.dumps(prop_val))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert data["status"] == "success"
        storm_ids = [s["storm_id"] for s in data["storms"]]
        assert "" not in storm_ids

    def test_corrupt_stress_storms_index_triggers_except(self, tmp_path, monkeypatch):
        """Line 75: corrupt _index.json → except Exception: pass."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        # Write invalid JSON to _index.json
        ss_dir = tmp_path / "stress_storms"
        ss_dir.mkdir()
        (ss_dir / "_index.json").write_text("NOT VALID JSON {{{")

        # Provide a gauge timeseries file so fallback path works
        gauge_ts = {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [{
                "storm_id": "STORM-FALLBACK",
                "exceeded_severe": True,
            }]},
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # Property with flooding
        prop_data = {
            "property_id": "PROP-001",
            "flood_events": [{"storm_id": "STORM-FALLBACK", "flood_depth_m": 0.3, "damage_ratio": 0.05}],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))
        prop_val = {"properties": [{"PropertyHeader": {"Header": {"PropertyID": "PROP-001"}}}]}
        (tmp_path / "property.json").write_text(json.dumps(prop_val))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert data["status"] == "success"
        # Falls back to gaugets path — should find STORM-FALLBACK
        storm_ids = [s["storm_id"] for s in data["storms"]]
        assert "STORM-FALLBACK" in storm_ids


class TestPropertyStormsMissingFiles:
    """Cover except blocks when storm_sequences.json or gauge.json missing."""

    def test_storms_without_storm_sequences_json(self, tmp_path, monkeypatch):
        """Lines 134-135: storm_sequences.json missing triggers except pass."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        # Property file exists but NO storm_sequences.json
        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0,
            "floor_level_m": 3.2,
            "nearest_gauges": [{"gauge_id": "GAUGE-001", "distance_m": 500}],
            "summary": {},
            "flood_events": [{"storm_id": "STORM-X", "sequence_id": "STORM-seqX",
                              "flood_depth_m": 0.5, "damage_ratio": 0.1}],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        # gauge.json exists so line 157 is covered normally
        gauge_data = {"flood_gauges": [{"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001"},
            "FloodStage": {"UK": {"FloodAlert": 4.0, "FloodWarning": 4.5,
                                  "SevereFloodWarning": 5.0}},
            "SensorDetails": {"GaugeInformation": {}},
        }}]}
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

        # storm_sequences.json does NOT exist → triggers except block
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/properties/PROP-001/storms")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        # Without storm_sequences.json, sequence_type defaults to 'isolated'
        assert data["flood_events"][0]["sequence_type"] == "isolated"

    def test_legacy_single_file_storm_artifacts(self, tmp_path, monkeypatch):
        """Legacy fallback: a portfolio with the pre-shard ``stress_storms.json``
        and ``storms.json`` single files (no _index.json / storm_sequences.json)
        still lists storms, enriched from the legacy metadata file."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        # Legacy single-file stress storms (no stress_storms/_index.json present).
        stress_storms = {"storms": [{
            "storm_id": "OLD-1", "name": "", "intensity_category": "",
            "effective_precipitation_mm": 0,
            "trigger_summary": {"gauges_severe": 2},
        }]}
        (tmp_path / "stress_storms.json").write_text(json.dumps(stress_storms))

        # Legacy single-file storm metadata (no storm_sequences.json present).
        legacy_storms = {"storms": [{
            "storm_id": "OLD-1", "name": "LegacyName",
            "intensity_category": "extreme", "effective_precipitation_mm": 99,
        }]}
        (tmp_path / "storms.json").write_text(json.dumps(legacy_storms))

        prop_data = {
            "property_id": "PROP-001",
            "flood_events": [{"storm_id": "OLD-1", "flood_depth_m": 0.5,
                              "damage_ratio": 0.1}],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))
        prop_val = {"properties": [{"PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "Valuation": {"PropertyValue": 400000},
        }}]}
        (tmp_path / "property.json").write_text(json.dumps(prop_val))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert data["status"] == "success"
        assert len(data["storms"]) == 1
        storm = data["storms"][0]
        assert storm["storm_id"] == "OLD-1"
        # Metadata merged in from the legacy storms.json
        assert storm["intensity_category"] == "extreme"
        assert storm["name"] == "LegacyName"
        assert storm["effective_precipitation_mm"] == 99
        assert storm["properties_flooded"] == 1
        assert storm["estimated_damage"] == 40000

    def test_gaugets_fallback_skips_non_gauge_files(self, tmp_path, monkeypatch):
        """Line 86: a stray non-``GAUGE-`` file in the gaugets collection is
        skipped during the gaugets fallback."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        # No stress storms at all → forces the gaugets fallback.
        gauge_ts = {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [{
                "storm_id": "STORM-FALLBACK", "exceeded_severe": True,
            }]},
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))
        # Stray non-GAUGE file that iter_keys yields but the route must skip.
        (gaugets_dir / "metadata.json").write_text(json.dumps({"junk": True}))

        prop_data = {
            "property_id": "PROP-001",
            "flood_events": [{"storm_id": "STORM-FALLBACK", "flood_depth_m": 0.3,
                              "damage_ratio": 0.05}],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))
        prop_val = {"properties": [{"PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"}}}]}
        (tmp_path / "property.json").write_text(json.dumps(prop_val))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert data["status"] == "success"
        storm_ids = [s["storm_id"] for s in data["storms"]]
        assert "STORM-FALLBACK" in storm_ids

    def test_storms_without_gauge_json(self, tmp_path, monkeypatch):
        """Lines 157-158: gauge.json missing triggers except pass."""
        from config import config

        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()

        prop_data = {
            "property_id": "PROP-001",
            "location": {"lat": 51.5, "lon": -0.12},
            "elevation_m": 3.0,
            "floor_level_m": 3.2,
            "nearest_gauges": [{"gauge_id": "GAUGE-001", "distance_m": 500}],
            "summary": {},
            "flood_events": [{"storm_id": "STORM-X",
                              "flood_depth_m": 0.5, "damage_ratio": 0.1}],
        }
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        # NO gauge.json → triggers except block on lines 157-158
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/properties/PROP-001/storms")
        assert r.status_code == 200
        data = r.get_json()
        # Without gauge.json, flood_stages should be empty dict
        for ng in data["nearest_gauges"]:
            assert ng["flood_stages"] == {}
