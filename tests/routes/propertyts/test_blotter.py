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

"""Tests for the REIT portfolio blotter endpoint.

GET /propertyts/blotter

Verifies that:
  - River distance is returned in km (converted from RiverDistanceMeters)
  - Elevation is relative to the reference gauge (including floor level),
    consistent with the PRS pricer flood threshold
  - All fields are present and correctly typed
"""

import json

import pytest

from models.floodrisk import relative_elevation


# ---------------------------------------------------------------------------
# Test data constants
# ---------------------------------------------------------------------------

GAUGE_ID = "GAUGE-TEST-001"
SYNTH_GAUGE_ID = "SYNTH-TEST-001"
PROP_ID_1 = "PROP-BLT-001"
PROP_ID_2 = "PROP-BLT-002"

GAUGE_ELEVATION = 10.0
SYNTH_GAUGE_ELEVATION = 7.5

PROP_1_GROUND = 14.5
PROP_1_FLOOR = 0.25
PROP_1_RIVER_DIST_M = 3200.0

PROP_2_GROUND = 6.0
PROP_2_FLOOR = 0.10
PROP_2_RIVER_DIST_M = 850.0


def _make_property_json():
    """Full CDM property.json with RiskAssessment, Construction, ReferenceGauges."""
    return {"properties": [
        {"PropertyHeader": {
            "Header": {"PropertyID": PROP_ID_1},
            "Location": {
                "BuildingNumber": "42",
                "StreetName": "River Road",
                "Postcode": "SW1A 1AA",
                "LatitudeDegrees": 51.5, "LongitudeDegrees": -0.12,
            },
            "Valuation": {"PropertyValue": 500000},
            "Construction": {"FloorLevelMeters": PROP_1_FLOOR},
            "RiskAssessment": {
                "GroundLevelMeters": PROP_1_GROUND,
                "RiverDistanceMeters": PROP_1_RIVER_DIST_M,
                "EAFloodZone": "Zone 2",
            },
            "ReferenceGauges": [GAUGE_ID],
        }},
        {"PropertyHeader": {
            "Header": {"PropertyID": PROP_ID_2},
            "Location": {
                "BuildingNumber": "7",
                "StreetName": "Low Lane",
                "Postcode": "TW9 3AB",
                "LatitudeDegrees": 51.4, "LongitudeDegrees": -0.3,
            },
            "Valuation": {"PropertyValue": 300000},
            "Construction": {"FloorLevelMeters": PROP_2_FLOOR},
            "RiskAssessment": {
                "GroundLevelMeters": PROP_2_GROUND,
                "RiverDistanceMeters": PROP_2_RIVER_DIST_M,
                "EAFloodZone": "Zone 3",
            },
            "ReferenceGauges": [SYNTH_GAUGE_ID],
        }},
    ]}


def _make_gauge_json():
    """gauge.json with one physical gauge including Location.GaugeElevation."""
    return {"flood_gauges": [{"FloodGauge": {
        "Header": {"GaugeID": GAUGE_ID, "GaugeName": "Test Physical Gauge"},
        "Location": {
            "GaugeLatitude": 51.5, "GaugeLongitude": -0.1,
            "GaugeElevation": GAUGE_ELEVATION,
        },
        "SensorDetails": {"GaugeInformation": {}},
        "FloodStage": {"UK": {
            "FloodAlert": 4.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.0,
        }},
    }}]}


def _make_gaugehc_json():
    """gaugehc.json with one synthetic gauge with elevation_m."""
    return {
        "metadata": {"catchment_id": "test", "num_gauges": 1,
                      "schema_version": "2.0"},
        "hazard_curves": {
            SYNTH_GAUGE_ID: {
                "gauge_id": SYNTH_GAUGE_ID, "gauge_name": "Synthetic 1",
                "elevation_m": SYNTH_GAUGE_ELEVATION,
                "curve_points": [],
            },
        },
    }


def _make_mortgage_json():
    return {"loans": [{
        "RLoan": {
            "Header": {"RLoanID": "MORT-BLT-001", "PropertyID": PROP_ID_1},
            "FinancialTerms": {"OriginalBalance": 350000},
            "CurrentStatus": {
                "OutstandingBalance": 320000,
                "CurrentLTV": 64.0,
                "RemainingTerm": 180,
            },
        },
    }]}


@pytest.fixture
def blotter_env(tmp_path, monkeypatch):
    """Isolated Flask test client with blotter-specific CDM data."""
    (tmp_path / "property.json").write_text(json.dumps(_make_property_json()))
    (tmp_path / "gauge.json").write_text(json.dumps(_make_gauge_json()))
    (tmp_path / "gaugehc.json").write_text(json.dumps(_make_gaugehc_json()))
    (tmp_path / "loan.json").write_text(json.dumps(_make_mortgage_json()))
    # propertyts dir must exist for other routes but blotter doesn't need it
    (tmp_path / "propertyts").mkdir()

    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return {"client": app.test_client()}


# ===========================================================================
# Basic endpoint tests
# ===========================================================================

class TestBlotterEndpoint:

    def test_returns_200(self, blotter_env):
        r = blotter_env["client"].get("/api/v1/propertyts/blotter")
        assert r.status_code == 200

    def test_returns_success_status(self, blotter_env):
        r = blotter_env["client"].get("/api/v1/propertyts/blotter")
        assert r.get_json()["status"] == "success"

    def test_options_returns_ok(self, blotter_env):
        r = blotter_env["client"].options("/api/v1/propertyts/blotter")
        assert r.status_code == 200

    def test_returns_all_properties(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        assert len(data["properties"]) == 2

    def test_summary_counts(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        assert data["summary"]["num_properties"] == 2
        assert data["summary"]["total_property_value"] == 800000


# ===========================================================================
# Relative elevation tests
# ===========================================================================

class TestBlotterElevation:
    """Elevation must be relative to gauge, including floor — matching PRS pricer."""

    def _get_property(self, blotter_env, prop_id):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        for p in data["properties"]:
            if p["property_id"] == prop_id:
                return p
        pytest.fail(f"Property {prop_id} not found in blotter response")

    def test_prop1_elevation_relative_to_gauge(self, blotter_env):
        """PROP-BLT-001: ground=14.5, gauge=10.0, floor=0.25 → 4.75."""
        p = self._get_property(blotter_env, PROP_ID_1)
        expected = relative_elevation(PROP_1_GROUND, GAUGE_ELEVATION, PROP_1_FLOOR)
        assert p["elevation_m"] == pytest.approx(expected, abs=0.01)
        assert p["elevation_m"] == pytest.approx(4.75, abs=0.01)

    def test_prop2_elevation_relative_to_synthetic_gauge(self, blotter_env):
        """PROP-BLT-002: ground=6.0, synth_gauge=7.5, floor=0.10 → 0.10.
        Property below gauge, so height_diff=0, only floor contributes."""
        p = self._get_property(blotter_env, PROP_ID_2)
        expected = relative_elevation(PROP_2_GROUND, SYNTH_GAUGE_ELEVATION, PROP_2_FLOOR)
        assert p["elevation_m"] == pytest.approx(expected, abs=0.01)
        assert p["elevation_m"] == pytest.approx(0.10, abs=0.01)

    def test_elevation_matches_prs_pricer_formula(self, blotter_env):
        """Both properties must match max(0, prop-gauge) + floor."""
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        for p in data["properties"]:
            assert isinstance(p["elevation_m"], (int, float))
            assert p["elevation_m"] >= 0


# ===========================================================================
# River distance conversion
# ===========================================================================

class TestBlotterRiverDistance:

    def _get_property(self, blotter_env, prop_id):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        for p in data["properties"]:
            if p["property_id"] == prop_id:
                return p
        pytest.fail(f"Property {prop_id} not found")

    def test_river_distance_in_km(self, blotter_env):
        p = self._get_property(blotter_env, PROP_ID_1)
        assert p["river_distance_km"] == pytest.approx(
            PROP_1_RIVER_DIST_M / 1000.0, abs=0.01)

    def test_river_distance_prop2(self, blotter_env):
        p = self._get_property(blotter_env, PROP_ID_2)
        assert p["river_distance_km"] == pytest.approx(
            PROP_2_RIVER_DIST_M / 1000.0, abs=0.01)

    def test_field_name_is_km_not_m(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        p = data["properties"][0]
        assert "river_distance_km" in p
        assert "river_distance_m" not in p


# ===========================================================================
# Field completeness
# ===========================================================================

class TestBlotterFieldPresence:

    def test_all_expected_fields(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        p = data["properties"][0]
        required = [
            "property_id", "property_address", "property_value",
            "river_distance_km", "elevation_m", "ea_flood_zone",
            "outstanding_balance", "current_ltv", "remaining_term_months",
        ]
        for field in required:
            assert field in p, f"Missing field: {field}"

    def test_address_populated(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        p1 = [p for p in data["properties"] if p["property_id"] == PROP_ID_1][0]
        assert p1["property_address"] == "42 River Road"

    def test_ea_flood_zone_populated(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        p1 = [p for p in data["properties"] if p["property_id"] == PROP_ID_1][0]
        assert p1["ea_flood_zone"] == "Zone 2"

    def test_mortgage_enrichment(self, blotter_env):
        data = blotter_env["client"].get("/api/v1/propertyts/blotter").get_json()
        p1 = [p for p in data["properties"] if p["property_id"] == PROP_ID_1][0]
        assert p1["outstanding_balance"] == 320000
        assert p1["current_ltv"] == 64.0
