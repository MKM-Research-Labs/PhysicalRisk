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
Data lineage tests for the REIT portfolio blotter elevation field.

Traces the elevation_m field through the full pipeline:

  property.json  CDM → PropertyHeader.RiskAssessment.GroundLevelMeters
                      → PropertyHeader.Construction.FloorLevelMeters
                      → PropertyHeader.ReferenceGauges[0]
  gauge.json     CDM → FloodGauge.Location.GaugeElevation
  gaugehc.json       → hazard_curves.<id>.elevation_m   (synthetic gauges)
                                     ↓
  relative_elevation(prop_ground, gauge_ground, floor)
                                     ↓
  /api/v1/propertyts/blotter  →  elevation_m  (relative, incl floor)
                                     ↓
  sp_table.py JS  →  Elevation (m) column

This is the same formula used by:
  - propagation.py  (flood threshold for depth calculation)
  - compound.py     (compound hydrograph threshold)
  - terrain_grid.py (PRS spread elevation adjustment)
"""

import json
from pathlib import Path

import pytest

from config import config
from models.floodrisk import relative_elevation


def _input_dir() -> Path:
    return config.get_input_dir()


# Disk-based lineage integration test: it reads the on-disk ``.json`` artifact
# tree directly with bare ``open()`` (no per-test guards). Skip when that tree is
# absent — under ``MKM_REPO_BACKEND=pg`` or a decommissioned tree the portfolio
# lives in the seam, not on disk, and lineage is not yet seam-aware (see
# test_lineage_backend_coupling.py). This turns a confusing FileNotFoundError
# into a clean skip.
pytestmark = pytest.mark.skipif(
    not (config.get_input_dir() / "property.json").is_file(),
    reason="requires the on-disk property.json artifact (file backend); "
    "skipped under pg backend / decommissioned tree",
)


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


# ===========================================================================
# Layer 1: CDM source fields exist
# ===========================================================================

class TestCDMElevationFields:
    """Verify property.json contains all fields required for relative elevation."""

    def _first_property(self):
        data = _load_json(_input_dir() / "property.json")
        return data["properties"][0]

    def test_risk_assessment_has_ground_level(self):
        p = self._first_property()
        risk = p["PropertyHeader"].get("RiskAssessment", {})
        assert "GroundLevelMeters" in risk
        assert isinstance(risk["GroundLevelMeters"], (int, float))
        assert risk["GroundLevelMeters"] > 0

    def test_risk_assessment_has_river_distance(self):
        p = self._first_property()
        risk = p["PropertyHeader"].get("RiskAssessment", {})
        assert "RiverDistanceMeters" in risk
        assert isinstance(risk["RiverDistanceMeters"], (int, float))
        assert risk["RiverDistanceMeters"] > 0

    def test_construction_has_floor_level(self):
        p = self._first_property()
        construction = p["PropertyHeader"].get("Construction", {})
        assert "FloorLevelMeters" in construction
        assert isinstance(construction["FloorLevelMeters"], (int, float))
        assert construction["FloorLevelMeters"] >= 0

    def test_has_reference_gauges(self):
        p = self._first_property()
        ref = p["PropertyHeader"].get("ReferenceGauges", [])
        assert len(ref) >= 1
        assert isinstance(ref[0], str)

    def test_risk_assessment_has_ea_flood_zone(self):
        p = self._first_property()
        risk = p["PropertyHeader"].get("RiskAssessment", {})
        assert "EAFloodZone" in risk


# ===========================================================================
# Layer 2: gauge elevation data exists
# ===========================================================================

class TestGaugeElevationFields:
    """Verify gauge.json and gaugehc.json contain elevation data."""

    def test_physical_gauge_has_elevation(self):
        data = _load_json(_input_dir() / "gauge.json")
        gauge = data["flood_gauges"][0]["FloodGauge"]
        loc = gauge.get("Location", {})
        assert "GaugeElevation" in loc
        assert isinstance(loc["GaugeElevation"], (int, float))

    def test_synthetic_gauge_has_elevation(self):
        data = _load_json(_input_dir() / "gaugehc.json")
        curves = data.get("hazard_curves", {})
        synth_ids = [k for k in curves if k.startswith("SYNTH-")]
        assert len(synth_ids) > 0, "No synthetic gauges found"
        first = curves[synth_ids[0]]
        assert "elevation_m" in first
        assert isinstance(first["elevation_m"], (int, float))


# ===========================================================================
# Layer 3: gauge ID cross-reference
# ===========================================================================

class TestGaugePropertyCrossRef:
    """Every property's ReferenceGauges must exist in gauge or gaugehc data."""

    def test_all_reference_gauges_resolvable(self):
        # Build lookup of all known gauge IDs
        known_gauges = set()
        try:
            data = _load_json(_input_dir() / "gauge.json")
            for fg in data.get("flood_gauges", []):
                gid = fg["FloodGauge"]["Header"]["GaugeID"]
                known_gauges.add(gid)
        except FileNotFoundError:
            pass
        try:
            data = _load_json(_input_dir() / "gaugehc.json")
            known_gauges.update(data.get("hazard_curves", {}).keys())
        except FileNotFoundError:
            pass

        # Check every property's reference gauge exists
        props = _load_json(_input_dir() / "property.json")
        missing = []
        for p in props["properties"]:
            ph = p["PropertyHeader"]
            pid = ph["Header"]["PropertyID"]
            for gid in ph.get("ReferenceGauges", []):
                if gid not in known_gauges:
                    missing.append(f"{pid} → {gid}")

        assert not missing, (
            f"Properties reference unknown gauges: {missing[:10]}"
        )


# ===========================================================================
# Layer 4: relative elevation consistency
# ===========================================================================

class TestElevationConsistency:
    """End-to-end: compute relative elevation from CDM and verify it matches
    the formula used by propagation.py and compound.py."""

    def _gauge_elevation_lookup(self):
        elevations = {}
        try:
            data = _load_json(_input_dir() / "gauge.json")
            for fg in data.get("flood_gauges", []):
                g = fg["FloodGauge"]
                gid = g["Header"]["GaugeID"]
                elevations[gid] = g.get("Location", {}).get(
                    "GaugeElevation", 0)
        except FileNotFoundError:
            pass
        try:
            data = _load_json(_input_dir() / "gaugehc.json")
            for gid, curve in data.get("hazard_curves", {}).items():
                if gid not in elevations:
                    elevations[gid] = curve.get("elevation_m", 0)
        except FileNotFoundError:
            pass
        return elevations

    def test_relative_elevation_always_non_negative(self):
        gauge_elev = self._gauge_elevation_lookup()
        props = _load_json(_input_dir() / "property.json")

        for p in props["properties"]:
            ph = p["PropertyHeader"]
            risk = ph.get("RiskAssessment", {})
            construction = ph.get("Construction", {})
            ref_gauges = ph.get("ReferenceGauges", [])

            prop_ground = risk.get("GroundLevelMeters", 0)
            floor = construction.get("FloorLevelMeters", 0)
            g_elev = gauge_elev.get(ref_gauges[0], 0) if ref_gauges else 0

            result = relative_elevation(prop_ground, g_elev, floor)
            assert result >= 0, (
                f"{ph['Header']['PropertyID']}: relative_elevation="
                f"{result} (prop={prop_ground}, gauge={g_elev}, floor={floor})"
            )

    def test_relative_elevation_matches_inline_formula(self):
        """Verify the utility matches the original inline calculation."""
        gauge_elev = self._gauge_elevation_lookup()
        props = _load_json(_input_dir() / "property.json")

        for p in props["properties"][:20]:
            ph = p["PropertyHeader"]
            risk = ph.get("RiskAssessment", {})
            construction = ph.get("Construction", {})
            ref_gauges = ph.get("ReferenceGauges", [])

            prop_ground = risk.get("GroundLevelMeters", 0)
            floor = construction.get("FloorLevelMeters", 0)
            g_elev = gauge_elev.get(ref_gauges[0], 0) if ref_gauges else 0

            # Original inline formula from propagation.py
            inline = max(0.0, prop_ground - g_elev) + floor
            utility = relative_elevation(prop_ground, g_elev, floor)

            assert utility == pytest.approx(inline, abs=1e-10), (
                f"{ph['Header']['PropertyID']}: utility={utility} != "
                f"inline={inline}"
            )

    def test_river_distance_positive_for_all_properties(self):
        props = _load_json(_input_dir() / "property.json")
        for p in props["properties"]:
            risk = p["PropertyHeader"].get("RiskAssessment", {})
            dist = risk.get("RiverDistanceMeters", 0)
            assert dist > 0, (
                f"{p['PropertyHeader']['Header']['PropertyID']}: "
                f"RiverDistanceMeters={dist}"
            )
