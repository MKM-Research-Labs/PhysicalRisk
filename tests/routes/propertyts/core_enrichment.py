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

"""Tests for routes/propertyts/core.py — list_flood_storms enrichment coverage."""

import json

import pytest

from .conftest import make_prop_file


class TestListFloodStormsEnrichment:
    """Cover list_flood_storms enrichment paths — lines 204-292."""

    def test_storm_with_empty_storm_id_skipped(self, tmp_path, monkeypatch):
        """Line 204: storm responses with empty storm_id are skipped."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [
                {"storm_id": "", "exceeded_severe": True},
                {"storm_id": "STORM-A", "exceeded_severe": True},
            ]},
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # Property flood data so STORM-A has properties_flooded > 0
        prop_data = {"property_id": "PROP-001",
                     "flood_events": [{"storm_id": "STORM-A",
                                       "flood_depth_m": 0.5, "damage_ratio": 0.1}]}
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        # No metadata files
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
        assert "" not in storm_ids
        assert "STORM-A" in storm_ids

    def test_gaugets_read_error_continues(self, tmp_path, monkeypatch):
        """Lines 218-219: invalid JSON in gaugets file triggers except continue."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        # One valid gauge, one broken
        good = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-B", "exceeded_severe": False}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(good))
        (gaugets_dir / "GAUGE-BAD.json").write_text("{invalid json")

        # Property flood data so STORM-B has properties_flooded > 0
        prop_data = {"property_id": "PROP-001",
                     "flood_events": [{"storm_id": "STORM-B",
                                       "flood_depth_m": 0.3, "damage_ratio": 0.05}]}
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

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
        assert data["count"] >= 1

    def test_storms_metadata_from_storms_json(self, tmp_path, monkeypatch):
        """Lines 235-237: storms.json enrichment path (not sequences)."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-C", "exceeded_severe": True}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # Property flood data so STORM-C has properties_flooded > 0
        prop_data = {"property_id": "PROP-001",
                     "flood_events": [{"storm_id": "STORM-C",
                                       "flood_depth_m": 0.6, "damage_ratio": 0.15}]}
        (pts_dir / "PROP-001.json").write_text(json.dumps(prop_data))

        # storms.json with 'storms' key (not 'sequences')
        storms_meta = {"storms": [
            {"storm_id": "STORM-C", "intensity_category": "extreme",
             "name": "BigStorm", "precipitation_mm": 80.0}
        ]}
        (tmp_path / "storms.json").write_text(json.dumps(storms_meta))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        storms = r.get_json()["storms"]
        s = [x for x in storms if x["storm_id"] == "STORM-C"][0]
        assert s["intensity_category"] == "extreme"
        assert s["effective_precipitation_mm"] == 80.0

    def test_storms_severity_classification_all_levels(self, tmp_path, monkeypatch):
        """Lines 254-266: storms without metadata get classified by gauges_severe count."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        # Create multiple gauges so we can vary gauges_severe
        storm_ids = ["S-CAT", "S-EXT", "S-SEV", "S-MOD", "S-BASE"]
        severe_counts = [10, 5, 2, 1, 0]

        for i, (sid, count) in enumerate(zip(storm_ids, severe_counts)):
            # Need 'count' gauges to mark this storm as severe
            for g in range(max(count, 1)):
                gid = f"GAUGE-{sid}-{g}"
                responses = [{"storm_id": sid,
                              "exceeded_severe": g < count}]
                # Also include all storms in each gauge for the 0-severe case
                if count == 0 and g == 0:
                    responses = [{"storm_id": sid, "exceeded_severe": False}]
                gauge_ts = {"gauge_id": gid,
                            "storm_responses": {"responses": responses}}
                (gaugets_dir / f"{gid}.json").write_text(json.dumps(gauge_ts))

        # Property flood data so storms have properties_flooded > 0
        for i, sid in enumerate(storm_ids):
            prop_data = {"property_id": f"PROP-{i:03d}",
                         "flood_events": [{"storm_id": sid,
                                           "flood_depth_m": 0.5, "damage_ratio": 0.1}]}
            (pts_dir / f"PROP-{i:03d}.json").write_text(json.dumps(prop_data))

        # No metadata files → classification happens on lines 254-266
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        storms = {s["storm_id"]: s for s in r.get_json()["storms"]}
        assert storms["S-CAT"]["intensity_category"] == "catastrophic"
        assert storms["S-CAT"]["name"] == "Catastrophic"
        assert storms["S-EXT"]["intensity_category"] == "extreme"
        assert storms["S-SEV"]["intensity_category"] == "severe"
        assert storms["S-MOD"]["intensity_category"] == "moderate"
        assert storms["S-BASE"]["intensity_category"] == "baseline"

    def test_property_flooding_enrichment(self, tmp_path, monkeypatch):
        """Lines 280-292: property flooding enriches storm with depth/damage."""
        from config import config

        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()

        gauge_ts = {"gauge_id": "G1", "storm_responses": {"responses": [
            {"storm_id": "STORM-D", "exceeded_severe": True}]}}
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

        # property.json with a valued property
        property_data = {"properties": [{
            "PropertyHeader": {"Header": {"PropertyID": "PROP-010"}}
        }]}
        (tmp_path / "property.json").write_text(json.dumps(property_data))

        # PROP file with positive flood depth
        prop_data = {
            "property_id": "PROP-010",
            "flood_events": [
                {"storm_id": "STORM-D", "flood_depth_m": 1.2, "damage_ratio": 0.35},
            ],
        }
        (pts_dir / "PROP-010.json").write_text(json.dumps(prop_data))

        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/propertyts/storms")
        storms = {s["storm_id"]: s for s in r.get_json()["storms"]}
        assert storms["STORM-D"]["properties_flooded"] == 1
        assert storms["STORM-D"]["max_depth_m"] == 1.2
        assert storms["STORM-D"]["max_damage_ratio"] == 0.35

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

        # PROP-B file exists but is not in valued_ids → skipped
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
        # PROP-B was skipped → properties_flooded=0 → storm filtered out
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

        # flood_depth_m = 0 → skipped
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
        # Zero depth → properties_flooded=0 → storm filtered out
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

        # property.json with invalid JSON → triggers except pass
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
