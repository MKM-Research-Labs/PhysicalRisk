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

"""Tests for routes/propertyts/core.py — storm filtering: valued IDs, zero depth, JSON errors."""

import json

import pytest

from .conftest import make_prop_file


class TestFloodStormsEnrichmentFiltering:
    """Storm filtering paths: not-in-valued-ids, zero depth, JSON read errors."""

    def test_property_not_in_valued_ids_skipped(self, tmp_path, monkeypatch):
        """Line 288: property not in valued_ids is skipped; storm filtered out."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-E", "exceeded_severe": False}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # property.json lists PROP-A only
        property_data = {"properties": [{
            "PropertyHeader": {"Header": {"PropertyID": "PROP-A"}}
        }]}
        (tmp_path / "property.json").write_text(json.dumps(property_data))

        # PROP-B file exists but is not in valued_ids -> skipped
        prop_data = {
            "property_id": "PROP-B",
            "flood_events": [
                {"storm_id": "STORM-E", "flood_depth_m": 0.8, "damage_ratio": 0.2},
            ],
        }
        (pts_dir / "PROP-B.json").write_text(json.dumps(prop_data))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        storm_ids = [s["storm_id"] for s in r.get_json()["storms"]]
        # PROP-B was skipped -> properties_flooded=0 -> storm filtered out
        assert "STORM-E" not in storm_ids

    def test_zero_flood_depth_skipped(self, tmp_path, monkeypatch):
        """Line 292: flood events with depth <= 0 are skipped; storm filtered out."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-F", "exceeded_severe": False}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        property_data = {"properties": [{
            "PropertyHeader": {"Header": {"PropertyID": "PROP-C"}}
        }]}
        (tmp_path / "property.json").write_text(json.dumps(property_data))

        # flood_depth_m = 0 -> skipped
        prop_data = {
            "property_id": "PROP-C",
            "flood_events": [
                {"storm_id": "STORM-F", "flood_depth_m": 0.0, "damage_ratio": 0.0},
            ],
        }
        (pts_dir / "PROP-C.json").write_text(json.dumps(prop_data))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        storm_ids = [s["storm_id"] for s in r.get_json()["storms"]]
        # Zero depth -> properties_flooded=0 -> storm filtered out
        assert "STORM-F" not in storm_ids

    def test_property_json_read_error_continues(self, tmp_path, monkeypatch):
        """Lines 280-281: property.json read error triggers except pass."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-G", "exceeded_severe": False}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # property.json with invalid JSON -> triggers except pass
        (tmp_path / "property.json").write_text("{bad json")

        # Property flood data — valued_ids is empty due to bad property.json,
        # so all PROP files are checked; STORM-G gets properties_flooded > 0
        prop_data = {"property_id": "PROP-001",
                     "flood_events": [{"storm_id": "STORM-G",
                                       "flood_depth_m": 0.4, "damage_ratio": 0.08}]}
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] >= 1

    def test_metadata_json_read_error_continues(self, tmp_path, monkeypatch):
        """Lines 235-239: invalid metadata JSON triggers except continue."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-H", "exceeded_severe": False}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # Property flood data so STORM-H has properties_flooded > 0
        prop_data = {"property_id": "PROP-001",
                     "flood_events": [{"storm_id": "STORM-H",
                                       "flood_depth_m": 0.3, "damage_ratio": 0.05}]}
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        # Invalid storm_sequences.json
        (tmp_path / "storm_sequences.json").write_text("{broken")

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        assert r.status_code == 200
