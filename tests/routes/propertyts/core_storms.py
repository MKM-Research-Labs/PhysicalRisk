# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for routes/propertyts/core.py — storm listing and missing-file edge cases."""

import json

import pytest


# ===========================================================================
# /propertyts/storms
# ===========================================================================

class TestListFloodStorms:

    def test_no_storms_file_returns_404(self, pts_client_no_data):
        r = pts_client_no_data.get("/api/v1/propertyts/storms")
        assert r.status_code == 404

    def test_with_data_returns_success(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert "storms" in data

    def test_options_returns_ok(self, pts_client_no_data):
        r = pts_client_no_data.options("/api/v1/propertyts/storms")
        assert r.status_code == 200

    def test_storms_list_count(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        data = r.get_json()
        assert data["count"] >= 1

    def test_storm_has_expected_fields(self, pts_env):
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        assert len(storms) >= 1
        s = storms[0]
        assert "storm_id" in s
        assert "properties_flooded" in s
        assert "gauges_severe" in s
        assert "max_depth_m" in s

    def test_storms_sorted_by_gauges_severe(self, pts_env):
        """Storms sorted by gauges_severe descending (most severe first)."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        counts = [s["gauges_severe"] for s in storms]
        assert counts == sorted(counts, reverse=True)

    def test_storm_name_from_intensity_category(self, pts_env):
        """Storm name is capitalised intensity_category, not empty."""
        r = pts_env["client"].get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        for s in storms:
            if s["intensity_category"]:
                assert s["name"] == s["intensity_category"].capitalize()


# ===========================================================================
# Coverage expansion — missing lines 134-135, 157-158
# ===========================================================================

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
