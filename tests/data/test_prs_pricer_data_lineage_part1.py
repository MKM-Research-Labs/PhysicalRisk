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


# Disk-based lineage integration test: it reads the on-disk ``.json`` artifact
# tree directly with bare ``open()``. Skip when that tree is absent — under
# ``MKM_REPO_BACKEND=pg`` or a decommissioned tree the portfolio lives in the
# seam, not on disk, and lineage is not yet seam-aware (see
# test_lineage_backend_coupling.py). This turns a confusing FileNotFoundError
# into a clean skip.
pytestmark = pytest.mark.skipif(
    not (config.get_input_dir() / "propertyhc.json").is_file(),
    reason="requires the on-disk propertyhc.json artifact (file backend); "
    "skipped under pg backend / decommissioned tree",
)


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
