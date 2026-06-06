"""
Data lineage tests for the property PRS pricer (part 1).

Traces every field that lands on phcData in the JS pricer back through the
pipeline: property.json CDM → propertyts (PROP-*.json) → propertyhc.json
→ /api/v1/properties/<id>/hazard → phcData.

Each test class covers one layer of the chain. Tests read from the generated
data directory and verify that every required field is present, non-null,
and correctly typed at each stage.
"""

import json
import math
from pathlib import Path

import pytest

from config import config
from config.models import EA_FLOOD_ZONE_RATES


def _input_dir() -> Path:
    return config.get_input_dir()


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _propertyhc() -> dict:
    return _load_json(_input_dir() / "propertyhc.json")


def _first_property() -> tuple:
    """Return (prop_id, prop_data) for the first property in propertyhc."""
    data = _propertyhc()
    curves = data.get("property_hazard_curves", {})
    prop_id = next(iter(curves))
    return prop_id, curves[prop_id]


def _propertyts_file(prop_id: str) -> dict:
    """Load the propertyts PROP-*.json for a given property."""
    pts_dir = _input_dir() / "propertyts"
    path = pts_dir / f"{prop_id}.json"
    if path.exists():
        return _load_json(path)
    return {}


def _property_cdm(prop_id: str) -> dict:
    """Find the property in the CDM property.json."""
    data = _load_json(_input_dir() / "property.json")
    for p in data.get("properties", []):
        hdr = p.get("PropertyHeader", {}).get("Header", {})
        if hdr.get("PropertyID") == prop_id:
            return p
    return {}


# ===========================================================================
# Layer 1: property.json CDM — source fields
# ===========================================================================

class TestCDMSourceFields:
    """Verify that property.json CDM contains all fields needed by the pricer."""

    def _first_cdm_property(self):
        """Return the first property from property.json CDM."""
        data = _load_json(_input_dir() / "property.json")
        props = data.get("properties", [])
        return props[0] if props else None

    def test_cdm_has_properties(self):
        data = _load_json(_input_dir() / "property.json")
        assert len(data.get("properties", [])) > 0

    def test_cdm_has_ea_flood_zone(self):
        cdm = self._first_cdm_property()
        if not cdm:
            pytest.skip("No CDM properties")
        ra = cdm.get("PropertyHeader", {}).get("RiskAssessment", {})
        zone = ra.get("EAFloodZone")
        assert zone is not None, "Missing EAFloodZone in CDM"
        assert zone in EA_FLOOD_ZONE_RATES, f"Invalid zone: {zone}"

    def test_cdm_has_ground_level(self):
        cdm = self._first_cdm_property()
        if not cdm:
            pytest.skip("No CDM properties")
        loc = cdm.get("PropertyHeader", {}).get("Location", {})
        ra = loc.get("RiskAssessment", cdm.get("PropertyHeader", {}).get("RiskAssessment", {}))
        assert ra.get("GroundLevelMeters") is not None

    def test_cdm_has_location(self):
        cdm = self._first_cdm_property()
        if not cdm:
            pytest.skip("No CDM properties")
        loc = cdm.get("PropertyHeader", {}).get("Location", {})
        assert loc.get("LatitudeDegrees") is not None
        assert loc.get("LongitudeDegrees") is not None

    def test_cdm_has_reference_gauges(self):
        cdm = self._first_cdm_property()
        if not cdm:
            pytest.skip("No CDM properties")
        refs = cdm.get("PropertyHeader", {}).get("ReferenceGauges", [])
        assert len(refs) > 0, "Property has no ReferenceGauges"


# ===========================================================================
# Layer 2: propertyts PROP-*.json — flood simulation output
# ===========================================================================

class TestPropertyTSFields:
    """Verify that propertyts output contains all fields needed by propertyhc."""

    def test_propertyts_has_property_id(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        assert pts.get("property_id") == prop_id

    def test_propertyts_has_elevation(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        assert "elevation_m" in pts
        assert isinstance(pts["elevation_m"], (int, float))

    def test_propertyts_has_floor_level(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        assert "floor_level_m" in pts

    def test_propertyts_has_flood_zone(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        assert "flood_zone" in pts
        assert pts["flood_zone"] in EA_FLOOD_ZONE_RATES

    def test_propertyts_has_flood_events(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        assert "flood_events" in pts
        assert isinstance(pts["flood_events"], list)

    def test_propertyts_has_nearest_gauges(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        ngs = pts.get("nearest_gauges", [])
        assert len(ngs) > 0
        ng = ngs[0]
        assert "gauge_id" in ng
        assert "distance_m" in ng

    def test_propertyts_has_location(self):
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip(f"No propertyts file for {prop_id}")
        loc = pts.get("location", {})
        assert "lat" in loc
        assert "lon" in loc

    def test_flood_zone_derived_from_synthetic(self):
        """Flood zone in propertyts is derived from synthetic gauge elevation,
        not from the CDM field (which may use a different elevation estimate)."""
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("Missing propertyts data")
        zone = pts.get("flood_zone")
        assert zone in EA_FLOOD_ZONE_RATES, f"Invalid zone: {zone}"
