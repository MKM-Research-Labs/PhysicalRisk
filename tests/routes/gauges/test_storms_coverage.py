"""Tests for stress_storms name enrichment in gauge storms endpoint (lines 113-119)."""

import json

from .conftest import GAUGE_ID, GAUGE_DATA, make_client


STORM_ID = "STORM-stress-001"


def _make_gaugets_with_storm_responses(storm_id):
    """Build gaugets data with storm_responses for a single storm."""
    return {
        "gauge_id": GAUGE_ID,
        "flood_simulation": {"readings": [{"waterLevel": 4.2}] * 168},
        "storm_responses": {
            "responses": [{
                "storm_id": storm_id,
                "base_level_m": 2.5,
                "level_change_m": 2.7,
                "peak_level_m": 5.2,
                "exceeded_alert": True,
                "exceeded_warning": True,
                "exceeded_severe": True,
            }]
        },
    }


class TestStressStormNameEnrichment:
    """Cover lines 113-119: loading storm names from stress_storms/_index.json."""

    def test_storm_name_enriched_from_stress_index(self, tmp_path, monkeypatch):
        """When stress_storms/_index.json has a named storm, that name appears
        in the response for matching storm_ids."""
        # Create stress_storms/_index.json with a named storm
        ss_dir = tmp_path / "stress_storms"
        ss_dir.mkdir()
        ss_index = {
            "storms": [{
                "storm_id": STORM_ID,
                "name": "Delta-181",
                "intensity_category": "severe",
            }]
        }
        (ss_dir / "_index.json").write_text(json.dumps(ss_index))

        # Create gaugets file with storm responses referencing the same storm_id
        gaugets_data = _make_gaugets_with_storm_responses(STORM_ID)

        client = make_client(
            tmp_path, monkeypatch,
            gaugets_file=gaugets_data,
        )

        resp = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"

        # The storm response should have the name from stress_storms
        responses = data["storm_responses"]["responses"]
        assert len(responses) >= 1
        matched = [r for r in responses if r.get("storm_id") == STORM_ID]
        assert len(matched) == 1
        assert matched[0]["name"] == "Delta-181"

    def test_storm_name_not_enriched_without_index(self, tmp_path, monkeypatch):
        """Without stress_storms/_index.json, storm names default to empty."""
        gaugets_data = _make_gaugets_with_storm_responses(STORM_ID)

        client = make_client(
            tmp_path, monkeypatch,
            gaugets_file=gaugets_data,
        )

        resp = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()
        responses = data["storm_responses"]["responses"]
        matched = [r for r in responses if r.get("storm_id") == STORM_ID]
        assert len(matched) == 1
        # Name should be empty string (no stress_storms index)
        assert matched[0]["name"] == ""

    def test_stress_index_storms_without_name_skipped(self, tmp_path, monkeypatch):
        """Storms in _index.json without a 'name' field are not added to storm_names."""
        ss_dir = tmp_path / "stress_storms"
        ss_dir.mkdir()
        ss_index = {
            "storms": [
                {"storm_id": STORM_ID},  # no 'name' key
                {"storm_id": "OTHER", "name": ""},  # empty name
            ]
        }
        (ss_dir / "_index.json").write_text(json.dumps(ss_index))

        gaugets_data = _make_gaugets_with_storm_responses(STORM_ID)

        client = make_client(
            tmp_path, monkeypatch,
            gaugets_file=gaugets_data,
        )

        resp = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()
        responses = data["storm_responses"]["responses"]
        matched = [r for r in responses if r.get("storm_id") == STORM_ID]
        assert len(matched) == 1
        assert matched[0]["name"] == ""

    def test_multiple_stress_storms_enriched(self, tmp_path, monkeypatch):
        """Multiple named storms in _index.json all get enriched."""
        storm_id_2 = "STORM-stress-002"
        ss_dir = tmp_path / "stress_storms"
        ss_dir.mkdir()
        ss_index = {
            "storms": [
                {"storm_id": STORM_ID, "name": "Delta-181"},
                {"storm_id": storm_id_2, "name": "Nu-56"},
            ]
        }
        (ss_dir / "_index.json").write_text(json.dumps(ss_index))

        # Gaugets with two storm responses
        gaugets_data = {
            "gauge_id": GAUGE_ID,
            "flood_simulation": {"readings": [{"waterLevel": 4.2}] * 168},
            "storm_responses": {
                "responses": [
                    {
                        "storm_id": STORM_ID,
                        "base_level_m": 2.5, "level_change_m": 2.7,
                        "peak_level_m": 5.2,
                        "exceeded_alert": True, "exceeded_warning": True,
                        "exceeded_severe": True,
                    },
                    {
                        "storm_id": storm_id_2,
                        "base_level_m": 2.5, "level_change_m": 1.5,
                        "peak_level_m": 4.0,
                        "exceeded_alert": True, "exceeded_warning": False,
                        "exceeded_severe": False,
                    },
                ]
            },
        }

        client = make_client(
            tmp_path, monkeypatch,
            gaugets_file=gaugets_data,
        )

        resp = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert resp.status_code == 200
        data = resp.get_json()
        responses = data["storm_responses"]["responses"]

        names_by_id = {r["storm_id"]: r["name"] for r in responses}
        assert names_by_id[STORM_ID] == "Delta-181"
        assert names_by_id[storm_id_2] == "Nu-56"
