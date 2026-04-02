"""
Data lineage tests for the property PRS pricer.

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

    def test_cdm_has_properties(self):
        data = _load_json(_input_dir() / "property.json")
        assert len(data.get("properties", [])) > 0

    def test_cdm_has_ea_flood_zone(self):
        prop_id, _ = _first_property()
        cdm = _property_cdm(prop_id)
        ra = cdm.get("PropertyHeader", {}).get("RiskAssessment", {})
        zone = ra.get("EAFloodZone")
        assert zone is not None, f"{prop_id} missing EAFloodZone in CDM"
        assert zone in EA_FLOOD_ZONE_RATES, f"{prop_id} invalid zone: {zone}"

    def test_cdm_has_ground_level(self):
        prop_id, _ = _first_property()
        cdm = _property_cdm(prop_id)
        ra = cdm.get("PropertyHeader", {}).get("RiskAssessment", {})
        assert ra.get("GroundLevelMeters") is not None

    def test_cdm_has_location(self):
        prop_id, _ = _first_property()
        cdm = _property_cdm(prop_id)
        loc = cdm.get("PropertyHeader", {}).get("Location", {})
        assert loc.get("LatitudeDegrees") is not None
        assert loc.get("LongitudeDegrees") is not None

    def test_cdm_has_reference_gauges(self):
        prop_id, _ = _first_property()
        cdm = _property_cdm(prop_id)
        refs = cdm.get("PropertyHeader", {}).get("ReferenceGauges", [])
        assert len(refs) > 0, f"{prop_id} has no ReferenceGauges"


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

    def test_flood_zone_matches_cdm(self):
        """Flood zone in propertyts should match the CDM source."""
        prop_id, _ = _first_property()
        pts = _propertyts_file(prop_id)
        cdm = _property_cdm(prop_id)
        if not pts or not cdm:
            pytest.skip("Missing propertyts or CDM data")
        cdm_zone = cdm.get("PropertyHeader", {}).get("RiskAssessment", {}).get("EAFloodZone")
        assert pts.get("flood_zone") == cdm_zone


# ===========================================================================
# Layer 3: propertyhc.json — hazard curve and pricing output
# ===========================================================================

class TestPropertyHCFields:
    """Verify every phcData field in propertyhc.json property_hazard_curves."""

    def test_property_id(self):
        prop_id, pc = _first_property()
        assert pc.get("property_id") == prop_id

    def test_location(self):
        _, pc = _first_property()
        loc = pc.get("location", {})
        assert "lat" in loc or "latitude" in loc

    def test_elevation_m(self):
        _, pc = _first_property()
        assert "elevation_m" in pc
        assert isinstance(pc["elevation_m"], (int, float))

    def test_floor_level_m(self):
        _, pc = _first_property()
        assert "floor_level_m" in pc

    def test_flood_zone(self):
        _, pc = _first_property()
        assert "flood_zone" in pc
        assert pc["flood_zone"] in EA_FLOOD_ZONE_RATES

    def test_flood_count(self):
        _, pc = _first_property()
        assert "flood_count" in pc
        assert isinstance(pc["flood_count"], int)

    def test_has_gev(self):
        _, pc = _first_property()
        assert "has_gev" in pc
        assert isinstance(pc["has_gev"], bool)

    def test_pricing_method(self):
        _, pc = _first_property()
        assert pc.get("pricing_method") in ("gev", "floor")

    def test_min_spread_bps(self):
        _, pc = _first_property()
        assert pc.get("min_spread_bps") == 2.0

    def test_term_structure_exists(self):
        _, pc = _first_property()
        ts = pc.get("term_structure", {})
        assert "tenors" in ts
        assert isinstance(ts["tenors"], list)
        assert len(ts["tenors"]) >= 1

    def test_term_structure_has_severe(self):
        _, pc = _first_property()
        ts = pc.get("term_structure", {})
        assert "severe" in ts
        severe = ts["severe"]
        assert "survival" in severe
        assert "prs_spread_bps" in severe

    def test_survival_monotonically_decreasing(self):
        _, pc = _first_property()
        survival = pc.get("term_structure", {}).get("severe", {}).get("survival", [])
        if len(survival) < 2:
            pytest.skip("Not enough survival points")
        for i in range(len(survival) - 1):
            assert survival[i] >= survival[i + 1], (
                f"Survival not decreasing: S({i})={survival[i]} > S({i+1})={survival[i+1]}"
            )

    def test_spreads_non_negative(self):
        _, pc = _first_property()
        for trigger in ("any_flood", "moderate", "severe"):
            spreads = pc.get("term_structure", {}).get(trigger, {}).get("prs_spread_bps", [])
            for s in spreads:
                assert s >= 0, f"Negative spread {s} for {trigger}"

    def test_nearest_gauges(self):
        _, pc = _first_property()
        ngs = pc.get("nearest_gauges", [])
        assert len(ngs) >= 1
        ng = ngs[0]
        assert "gauge_id" in ng
        assert "distance_km" in ng
        assert "gauge_elevation_m" in ng

    def test_nearest_gauge_has_basis_bps(self):
        _, pc = _first_property()
        ngs = pc.get("nearest_gauges", [])
        for ng in ngs:
            basis = ng.get("basis_bps", {})
            assert "severe" in basis, f"Gauge {ng['gauge_id']} missing severe basis"
            assert "values" in basis["severe"]
            assert len(basis["severe"]["values"]) >= 1

    def test_nearest_gauge_has_flood_counts(self):
        _, pc = _first_property()
        ngs = pc.get("nearest_gauges", [])
        for ng in ngs:
            assert "property_flood_count" in ng
            assert "gauge_flood_count" in ng
            assert "flood_transmission_rate" in ng

    def test_depth_thresholds(self):
        _, pc = _first_property()
        dt = pc.get("depth_thresholds", {})
        for trigger in ("any_flood", "moderate", "severe"):
            assert trigger in dt, f"Missing depth threshold: {trigger}"
            assert "annual_probability" in dt[trigger]
            assert "threshold_m" in dt[trigger]

    def test_summary(self):
        _, pc = _first_property()
        summary = pc.get("summary", {})
        assert "avg_basis_bps" in summary
        assert "flood_transmission_rate" in summary

    def test_gev_params_when_has_gev(self):
        _, pc = _first_property()
        if not pc.get("has_gev"):
            pytest.skip("Property does not have GEV fit")
        params = pc.get("gev_params", {})
        assert "shape" in params
        assert "loc" in params
        assert "scale" in params

    def test_flood_zone_matches_propertyts(self):
        """Flood zone in propertyhc should match the propertyts source."""
        prop_id, pc = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("No propertyts file")
        assert pc.get("flood_zone") == pts.get("flood_zone")


# ===========================================================================
# Layer 4: spread_decomposition — post-processing attachment
# ===========================================================================

class TestSpreadDecompositionLineage:
    """Verify spread_decomposition fields in propertyhc.json."""

    def _get_decomp(self):
        _, pc = _first_property()
        sd = pc.get("spread_decomposition")
        if not sd:
            pytest.skip("spread_decomposition not attached")
        return sd

    def test_gauge_spread_present(self):
        sd = self._get_decomp()
        assert "gauge_spread_bps" in sd
        assert isinstance(sd["gauge_spread_bps"], (int, float))

    def test_property_spread_present(self):
        sd = self._get_decomp()
        assert "property_spread_bps" in sd

    def test_shd_spread_present(self):
        sd = self._get_decomp()
        assert "shd_spread_bps" in sd

    def test_she_spread_present(self):
        sd = self._get_decomp()
        assert "she_spread_bps" in sd

    def test_distance_first_path(self):
        sd = self._get_decomp()
        df = sd.get("distance_first", {})
        assert "distance_effect_bps" in df
        assert "elevation_effect_bps" in df

    def test_elevation_first_path(self):
        sd = self._get_decomp()
        ef = sd.get("elevation_first", {})
        assert "elevation_effect_bps" in ef
        assert "distance_effect_bps" in ef

    def test_distance_first_sums_to_basis(self):
        sd = self._get_decomp()
        gauge = sd["gauge_spread_bps"]
        prop = sd["property_spread_bps"]
        df = sd["distance_first"]
        total = gauge + df["distance_effect_bps"] + df["elevation_effect_bps"]
        assert abs(total - prop) < 0.5, (
            f"Distance-first path: {gauge} + {df['distance_effect_bps']} + "
            f"{df['elevation_effect_bps']} = {total} != {prop}"
        )

    def test_elevation_first_sums_to_basis(self):
        sd = self._get_decomp()
        gauge = sd["gauge_spread_bps"]
        prop = sd["property_spread_bps"]
        ef = sd["elevation_first"]
        total = gauge + ef["elevation_effect_bps"] + ef["distance_effect_bps"]
        assert abs(total - prop) < 0.5, (
            f"Elevation-first path: {gauge} + {ef['elevation_effect_bps']} + "
            f"{ef['distance_effect_bps']} = {total} != {prop}"
        )

    def test_shd_she_source_files_exist(self):
        """propertyshd.json and propertyshe.json must exist for decomposition."""
        shd = _input_dir() / "propertyshd.json"
        she = _input_dir() / "propertyshe.json"
        assert shd.exists(), "propertyshd.json missing — run: python app.py port --propertyshd"
        assert she.exists(), "propertyshe.json missing — run: python app.py port --propertyshe"

    def test_property_spread_matches_term_structure(self):
        """property_spread_bps should equal the 5yr severe spread from term_structure."""
        prop_id, pc = _first_property()
        sd = pc.get("spread_decomposition")
        if not sd:
            pytest.skip("No decomposition")
        ts_spreads = pc.get("term_structure", {}).get("severe", {}).get("prs_spread_bps", [])
        if len(ts_spreads) < 5:
            pytest.skip("Not enough tenor points")
        assert abs(sd["property_spread_bps"] - ts_spreads[4]) < 0.1


# ===========================================================================
# Layer 5: metadata — terrain grid
# ===========================================================================

class TestTerrainGridInMetadata:
    """Verify terrain_grid in propertyhc.json metadata."""

    def test_metadata_has_terrain_grid(self):
        data = _propertyhc()
        grid = data.get("metadata", {}).get("terrain_grid")
        assert grid is not None, "terrain_grid missing from metadata"

    def test_terrain_grid_distances(self):
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        assert len(grid["distances"]) == 21
        assert grid["distances"][0] == 0
        assert grid["distances"][-1] == 5000

    def test_terrain_grid_elevations(self):
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        assert len(grid["elevations"]) == 11
        assert grid["elevations"][0] == 0.0
        assert grid["elevations"][-1] == 5.0

    def test_terrain_grid_has_all_zones(self):
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        assert set(grid["zones"].keys()) == set(EA_FLOOD_ZONE_RATES.keys())

    def test_terrain_grid_zone_dimensions(self):
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        for zone, zdata in grid["zones"].items():
            assert len(zdata["grid"]) == 21, f"{zone} wrong distance dim"
            for row in zdata["grid"]:
                assert len(row) == 11, f"{zone} wrong elevation dim"

    def test_terrain_grid_zone3b_gt_zone1_at_origin(self):
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        s3b = grid["zones"]["Zone 3b"]["grid"][0][0]
        s1 = grid["zones"]["Zone 1"]["grid"][0][0]
        assert s3b > s1

    def test_terrain_grid_spot_check_against_analytical(self):
        """Spot-check grid value against direct compute_prs_spread call."""
        from models.hazard.prs_analytical import compute_prs_spread
        from models.floodrisk.velocity import compute_retention

        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        # Zone 2 at d=1000m (idx 4), h=1.0m (idx 2)
        zone_rate = 0.005
        ret = compute_retention(1000)
        elev_factor = math.exp(-1.0 / 2.0)
        prop_rate = zone_rate * ret * elev_factor
        expected = round(compute_prs_spread(prop_rate, tenor=5, recovery=0.0,
                                             risk_free_rate=0.03), 2)
        actual = grid["zones"]["Zone 2"]["grid"][4][2]
        assert abs(actual - expected) < 0.01, f"Grid={actual} vs analytical={expected}"


# ===========================================================================
# Layer 6: cross-layer consistency
# ===========================================================================

class TestCrossLayerConsistency:
    """Verify data flows consistently across pipeline layers."""

    def test_elevation_cdm_to_propertyhc(self):
        """Elevation should trace: CDM → propertyts → propertyhc."""
        prop_id, pc = _first_property()
        cdm = _property_cdm(prop_id)
        pts = _propertyts_file(prop_id)
        if not cdm or not pts:
            pytest.skip("Missing CDM or propertyts data")
        cdm_elev = cdm.get("PropertyHeader", {}).get("RiskAssessment", {}).get("GroundLevelMeters")
        pts_elev = pts.get("elevation_m")
        hc_elev = pc.get("elevation_m")
        if cdm_elev is not None and pts_elev is not None:
            assert abs(pts_elev - cdm_elev) < 0.01
        if pts_elev is not None and hc_elev is not None:
            assert abs(hc_elev - pts_elev) < 0.01

    def test_flood_zone_cdm_to_propertyhc(self):
        """Flood zone should trace: CDM → propertyts → propertyhc."""
        prop_id, pc = _first_property()
        cdm = _property_cdm(prop_id)
        pts = _propertyts_file(prop_id)
        if not cdm or not pts:
            pytest.skip("Missing CDM or propertyts data")
        cdm_zone = cdm.get("PropertyHeader", {}).get("RiskAssessment", {}).get("EAFloodZone")
        pts_zone = pts.get("flood_zone")
        hc_zone = pc.get("flood_zone")
        assert cdm_zone == pts_zone == hc_zone, (
            f"Zone mismatch: CDM={cdm_zone} → PTS={pts_zone} → HC={hc_zone}"
        )

    def test_gauge_ids_propertyts_to_propertyhc(self):
        """Nearest gauge IDs should carry through from propertyts to propertyhc."""
        prop_id, pc = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("No propertyts file")
        pts_gauges = {ng["gauge_id"] for ng in pts.get("nearest_gauges", [])}
        hc_gauges = {ng["gauge_id"] for ng in pc.get("nearest_gauges", [])
                     if not ng["gauge_id"].startswith("SYNTH")}
        # HC gauges should be a subset of (or equal to) PTS gauges
        assert hc_gauges.issubset(pts_gauges), (
            f"HC gauges {hc_gauges} not subset of PTS gauges {pts_gauges}"
        )

    def test_flood_count_matches_propertyts_events(self):
        """flood_count in propertyhc should match flooded event count in propertyts."""
        prop_id, pc = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("No propertyts file")
        pts_flooded = len([e for e in pts.get("flood_events", [])
                           if e.get("flooded", False)])
        assert pc.get("flood_count") == pts_flooded

    def test_all_properties_have_complete_phcdata(self):
        """Every property in propertyhc should have all fields the pricer needs."""
        data = _propertyhc()
        required = [
            "property_id", "elevation_m", "floor_level_m", "flood_zone",
            "flood_count", "has_gev", "pricing_method", "min_spread_bps",
            "term_structure", "nearest_gauges", "summary",
        ]
        curves = data.get("property_hazard_curves", {})
        for prop_id, pc in curves.items():
            for field in required:
                assert field in pc, f"{prop_id} missing required field: {field}"
