# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for property hazard curve routes (propertyhc.py).

Covers:
  GET /api/v1/propertyhc/summary     — portfolio-wide hazard summary
  GET /api/v1/properties/<id>/hazard — per-property hazard + PRS + basis
  GET /api/v1/propertyhc/basis       — basis table across all properties

Tests are grouped by endpoint with 404 (no data), OPTIONS, happy path,
response structure, and edge-case sub-classes for each.
"""

import json
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_PROPERTYHC = {
    "metadata": {
        "generated_at": "2026-01-01T00:00:00",
        "catchment": "thames",
        "num_properties": 2,
    },
    "summary": {
        "total_properties": 2,
        "avg_flood_count": 3.5,
    },
    "property_hazard_curves": {
        "PROP-001": {
            "property_id": "PROP-001",
            "flood_count": 4,
            "summary": {
                "avg_basis_bps": 5.2,
                "flood_transmission_rate": 0.08,
                "max_depth_m": 0.65,
            },
            "nearest_gauges": [
                {
                    "gauge_id": "GAUGE-AAA",
                    "distance_km": 1.2,
                    "event_basis": 4.8,
                    "flood_transmission_rate": 0.07,
                }
            ],
            "hazard_curve": [[0.1, 0.05], [0.5, 0.01]],
        },
        "PROP-002": {
            "property_id": "PROP-002",
            "flood_count": 3,
            "summary": {
                "avg_basis_bps": 3.1,
                "flood_transmission_rate": 0.06,
                "max_depth_m": 0.3,
            },
            "nearest_gauges": [
                {
                    "gauge_id": "GAUGE-BBB",
                    "distance_km": 0.8,
                    "event_basis": 2.9,
                    "flood_transmission_rate": 0.05,
                }
            ],
            "hazard_curve": [[0.1, 0.03]],
        },
    },
}


@pytest.fixture
def phc_client_no_data(tmp_path, monkeypatch):
    """Client where propertyhc.json does not exist."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def phc_env(tmp_path, monkeypatch):
    """Client with a minimal propertyhc.json in tmp_path."""
    from config import config
    (tmp_path / "propertyhc.json").write_text(json.dumps(SAMPLE_PROPERTYHC))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# GET /api/v1/propertyhc/summary
# ---------------------------------------------------------------------------

class TestPropertyhcSummary:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/summary")
        assert r.status_code == 404

    def test_no_data_status_is_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/summary")
        assert r.get_json()["status"] == "error"

    def test_no_data_message_mentions_command(self, phc_client_no_data):
        msg = r.get_json()["message"] if (r := phc_client_no_data.get("/api/v1/propertyhc/summary")) else ""
        r = phc_client_no_data.get("/api/v1/propertyhc/summary")
        assert "port" in r.get_json()["message"].lower() or "propertyhc" in r.get_json()["message"].lower()

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/summary")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/summary")
        assert r.get_json()["status"] == "ok"

    def test_returns_200_with_data(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert r.status_code == 200

    def test_status_is_success(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert r.get_json()["status"] == "success"

    def test_response_has_data_key(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "data" in r.get_json()

    def test_response_has_metadata(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "metadata" in r.get_json()["data"]

    def test_response_has_summary(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "summary" in r.get_json()["data"]

    def test_response_has_distribution(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        assert "distribution" in r.get_json()["data"]

    def test_distribution_num_properties(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert dist["num_properties"] == 2

    def test_distribution_avg_basis_bps(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert "avg_basis_bps" in dist
        assert dist["avg_basis_bps"] >= 0

    def test_distribution_avg_flood_count(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert "avg_flood_count" in dist
        assert dist["avg_flood_count"] > 0

    def test_distribution_max_depth_m(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/summary")
        dist = r.get_json()["data"]["distribution"]
        assert "max_depth_m" in dist
        assert dist["max_depth_m"] > 0


class TestPropertyhcSummaryEmpty:
    """Summary when all properties have no flood events or summary data."""

    @pytest.fixture
    def phc_empty_curves(self, tmp_path, monkeypatch):
        from config import config
        data = {
            "metadata": {},
            "summary": {},
            "property_hazard_curves": {},
        }
        (tmp_path / "propertyhc.json").write_text(json.dumps(data))
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_empty_curves_returns_200(self, phc_empty_curves):
        r = phc_empty_curves.get("/api/v1/propertyhc/summary")
        assert r.status_code == 200

    def test_empty_curves_num_properties_is_zero(self, phc_empty_curves):
        r = phc_empty_curves.get("/api/v1/propertyhc/summary")
        assert r.get_json()["data"]["distribution"]["num_properties"] == 0

    def test_empty_curves_avg_flood_count_is_zero(self, phc_empty_curves):
        r = phc_empty_curves.get("/api/v1/propertyhc/summary")
        assert r.get_json()["data"]["distribution"]["avg_flood_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/v1/properties/<prop_id>/hazard
# ---------------------------------------------------------------------------

class TestPropertyHazard:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/hazard")
        assert r.status_code == 404

    def test_no_data_status_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["status"] == "error"

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/hazard")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["status"] == "ok"

    def test_unknown_property_returns_404(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-GHOST/hazard")
        assert r.status_code == 404

    def test_unknown_property_status_error(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-GHOST/hazard")
        assert r.get_json()["status"] == "error"

    def test_unknown_property_message_contains_id(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-GHOST/hazard")
        assert "PROP-GHOST" in r.get_json()["message"]

    def test_known_property_returns_200(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert r.status_code == 200

    def test_known_property_status_success(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["status"] == "success"

    def test_response_has_data_key(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "data" in r.get_json()

    def test_data_contains_property_id(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert r.get_json()["data"]["property_id"] == "PROP-001"

    def test_data_contains_hazard_curve(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "hazard_curve" in r.get_json()["data"]

    def test_data_contains_summary(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "summary" in r.get_json()["data"]

    def test_data_contains_nearest_gauges(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-001/hazard")
        assert "nearest_gauges" in r.get_json()["data"]

    def test_second_property_also_works(self, phc_env):
        r = phc_env.get("/api/v1/properties/PROP-002/hazard")
        assert r.status_code == 200
        assert r.get_json()["data"]["property_id"] == "PROP-002"


# ---------------------------------------------------------------------------
# GET /api/v1/propertyhc/basis
# ---------------------------------------------------------------------------

class TestPropertyhcBasis:

    def test_no_data_returns_404(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/basis")
        assert r.status_code == 404

    def test_no_data_status_error(self, phc_client_no_data):
        r = phc_client_no_data.get("/api/v1/propertyhc/basis")
        assert r.get_json()["status"] == "error"

    def test_options_returns_200(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/basis")
        assert r.status_code == 200

    def test_options_status_ok(self, phc_client_no_data):
        r = phc_client_no_data.options("/api/v1/propertyhc/basis")
        assert r.get_json()["status"] == "ok"

    def test_returns_200_with_data(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert r.status_code == 200

    def test_status_is_success(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert r.get_json()["status"] == "success"

    def test_response_has_count(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert "count" in r.get_json()

    def test_response_has_basis_table(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert "basis_table" in r.get_json()

    def test_basis_table_count_matches(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        data = r.get_json()
        assert data["count"] == len(data["basis_table"])

    def test_basis_table_length(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        assert r.get_json()["count"] == 2

    def test_basis_entry_has_property_id(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "property_id" in entry

    def test_basis_entry_has_flood_count(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "flood_count" in entry

    def test_basis_entry_has_avg_basis_bps(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "avg_basis_bps" in entry

    def test_basis_entry_has_nearest_gauges(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        assert "nearest_gauges" in entry

    def test_basis_table_sorted_desc_by_basis(self, phc_env):
        """Results must be sorted highest avg_basis_bps first."""
        r = phc_env.get("/api/v1/propertyhc/basis")
        table = r.get_json()["basis_table"]
        bases = [e["avg_basis_bps"] for e in table]
        assert bases == sorted(bases, reverse=True)

    def test_nearest_gauge_has_gauge_id(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        if entry["nearest_gauges"]:
            assert "gauge_id" in entry["nearest_gauges"][0]

    def test_nearest_gauge_has_distance_km(self, phc_env):
        r = phc_env.get("/api/v1/propertyhc/basis")
        entry = r.get_json()["basis_table"][0]
        if entry["nearest_gauges"]:
            assert "distance_km" in entry["nearest_gauges"][0]


class TestPropertyhcBasisEmpty:

    @pytest.fixture
    def phc_empty_basis(self, tmp_path, monkeypatch):
        from config import config
        data = {"metadata": {}, "summary": {}, "property_hazard_curves": {}}
        (tmp_path / "propertyhc.json").write_text(json.dumps(data))
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        return app.test_client()

    def test_empty_returns_200(self, phc_empty_basis):
        r = phc_empty_basis.get("/api/v1/propertyhc/basis")
        assert r.status_code == 200

    def test_empty_count_is_zero(self, phc_empty_basis):
        r = phc_empty_basis.get("/api/v1/propertyhc/basis")
        assert r.get_json()["count"] == 0

    def test_empty_basis_table_is_list(self, phc_empty_basis):
        r = phc_empty_basis.get("/api/v1/propertyhc/basis")
        assert isinstance(r.get_json()["basis_table"], list)
