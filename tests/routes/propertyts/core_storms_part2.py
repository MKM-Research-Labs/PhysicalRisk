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
