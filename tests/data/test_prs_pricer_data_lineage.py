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

    def test_pricing_method_is_event_count(self):
        _, pc = _first_property()
        assert pc.get("pricing_method") == "event_count"

    def test_has_gev_is_false(self):
        _, pc = _first_property()
        assert pc.get("has_gev") is False

    def test_gev_params_is_none(self):
        _, pc = _first_property()
        assert pc.get("gev_params") is None

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
        assert "prs_spread_bps" in severe

    def test_term_structure_is_flat(self):
        """All tenors should have the same spread (storms are independent)."""
        _, pc = _first_property()
        spreads = pc.get("term_structure", {}).get("severe", {}).get("prs_spread_bps", [])
        if len(spreads) < 2:
            pytest.skip("Not enough tenor points")
        assert all(s == spreads[0] for s in spreads), (
            f"Term structure not flat: {spreads}"
        )

    def test_spread_equals_event_count_formula(self):
        """Spread should equal flood_count / num_storms * 10000."""
        _, pc = _first_property()
        flood_count = pc.get("flood_count", 0)
        dt = pc.get("depth_thresholds", {}).get("severe", {})
        annual_prob = dt.get("annual_probability", 0)
        spreads = pc.get("term_structure", {}).get("severe", {}).get("prs_spread_bps", [])
        if not spreads:
            pytest.skip("No spread data")
        expected = round(annual_prob * 10000, 2)
        assert abs(spreads[0] - expected) < 0.1, (
            f"Spread {spreads[0]} != annual_prob * 10000 = {expected}"
        )

    def test_spreads_non_negative(self):
        _, pc = _first_property()
        spreads = pc.get("term_structure", {}).get("severe", {}).get("prs_spread_bps", [])
        for s in spreads:
            assert s >= 0, f"Negative spread {s}"

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
        assert "severe" in dt, "Missing severe depth threshold"
        assert "annual_probability" in dt["severe"]

    def test_only_severe_threshold(self):
        """Only severe threshold should exist (no any_flood or moderate)."""
        _, pc = _first_property()
        dt = pc.get("depth_thresholds", {})
        assert set(dt.keys()) == {"severe"}, f"Unexpected thresholds: {set(dt.keys())}"

    def test_summary(self):
        _, pc = _first_property()
        summary = pc.get("summary", {})
        assert "avg_basis_bps" in summary
        assert "flood_transmission_rate" in summary

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

    def test_terrain_grid_zone_ordering_at_origin(self):
        """Zone 3b spread > Zone 3a > Zone 2 > Zone 1 at origin (d=0, h=0)."""
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        s3b = grid["zones"]["Zone 3b"]["grid"][0][0]
        s3a = grid["zones"]["Zone 3a"]["grid"][0][0]
        s2 = grid["zones"]["Zone 2"]["grid"][0][0]
        s1 = grid["zones"]["Zone 1"]["grid"][0][0]
        assert s3b > s3a > s2 > s1, (
            f"Zone ordering wrong at origin: 3b={s3b}, 3a={s3a}, 2={s2}, 1={s1}"
        )

    def test_terrain_grid_spread_decreases_with_distance(self):
        """Spread should decrease with distance for a given zone/elevation."""
        data = _propertyhc()
        grid = data["metadata"]["terrain_grid"]
        g = grid["zones"]["Zone 3a"]["grid"]
        # Elevation index 0 (h=0), distances 0..5000m
        for i in range(len(g) - 1):
            assert g[i][0] >= g[i + 1][0], (
                f"Spread not decreasing with distance at idx {i}: {g[i][0]} < {g[i+1][0]}"
            )


# ===========================================================================
# Layer 6: cross-layer consistency
# ===========================================================================

class TestCrossLayerConsistency:
    """Verify data flows consistently across pipeline layers."""

    def test_elevation_propertyts_to_propertyhc(self):
        """Elevation should be consistent between propertyts and propertyhc.
        Note: may differ from CDM due to elevation sanity check (property
        lifted above gauge if below river level)."""
        prop_id, pc = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("Missing propertyts data")
        pts_elev = pts.get("elevation_m")
        hc_elev = pc.get("elevation_m")
        if pts_elev is not None and hc_elev is not None:
            assert abs(hc_elev - pts_elev) < 0.01

    def test_flood_zone_propertyts_to_propertyhc(self):
        """Flood zone should be consistent between propertyts and propertyhc.
        Zone is derived from synthetic gauge elevation in propertyts, not
        from the CDM field."""
        prop_id, pc = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("Missing propertyts data")
        pts_zone = pts.get("flood_zone")
        hc_zone = pc.get("flood_zone")
        assert pts_zone == hc_zone, (
            f"Zone mismatch: PTS={pts_zone} → HC={hc_zone}"
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

    def test_flood_count_matches_propertyts_severe_events(self):
        """flood_count in propertyhc should match severe-flooded event count in propertyts.

        flood_count uses the severe-only definition: flooded AND exceeded_severe.
        Re-run `python3 app.py port` if propertyts data is stale.
        """
        prop_id, pc = _first_property()
        pts = _propertyts_file(prop_id)
        if not pts:
            pytest.skip("No propertyts file")
        events = pts.get("flood_events", [])
        if events and "exceeded_severe" not in events[0]:
            pytest.skip("Stale propertyts data — re-run: python3 app.py port")
        pts_severe_flooded = len([
            e for e in events
            if e.get("flooded", False) and e.get("exceeded_severe", False)
        ])
        assert pc.get("flood_count") == pts_severe_flooded, (
            f"flood_count={pc.get('flood_count')} but propertyts has "
            f"{pts_severe_flooded} severe-flooded events"
        )

    def test_flood_count_consistent_with_marker_color_source(self):
        """The flood_count used by marker colors must equal the PRS pricer's count.

        This lineage test ensures the property layer (marker coloring) and
        PRS pricer always display the same flood count — both read the
        top-level flood_count from propertyhc.json, which must use the
        severe-only definition (flooded AND exceeded_severe).
        """
        data = _propertyhc()
        curves = data.get("property_hazard_curves", {})
        for prop_id, pc in curves.items():
            flood_count = pc.get("flood_count", 0)
            # Spread should be exactly flood_count / num_storms * 10000
            num_storms = data.get("metadata", {}).get("num_storms", 0)
            if num_storms == 0:
                continue
            spreads = pc.get("term_structure", {}).get("severe", {}).get("prs_spread_bps", [])
            if not spreads:
                continue
            expected_spread = round((flood_count / num_storms) * 10000, 2)
            assert spreads[0] == expected_spread, (
                f"{prop_id}: marker flood_count={flood_count} implies spread "
                f"{expected_spread}bp but PRS has {spreads[0]}bp"
            )

    def test_all_properties_have_complete_phcdata(self):
        """Every property in propertyhc should have all fields the pricer needs."""
        data = _propertyhc()
        required = [
            "property_id", "elevation_m", "floor_level_m", "flood_zone",
            "flood_count", "pricing_method",
            "term_structure", "nearest_gauges", "summary",
        ]
        curves = data.get("property_hazard_curves", {})
        for prop_id, pc in curves.items():
            for field in required:
                assert field in pc, f"{prop_id} missing required field: {field}"


# ===========================================================================
# Layer 7: Economic sanity — zone/spread consistency
# ===========================================================================

class TestZoneSpreadConsistency:
    """Verify that EA flood zone correlates with flood risk and spreads."""

    def _zone_stats(self):
        """Collect per-zone statistics across all properties."""
        data = _propertyhc()
        curves = data.get("property_hazard_curves", {})
        stats = {}
        for prop_id, pc in curves.items():
            zone = pc.get("flood_zone", "Unknown")
            if zone not in stats:
                stats[zone] = {"flood_counts": [], "spreads": [], "elevations": []}
            stats[zone]["flood_counts"].append(pc.get("flood_count", 0))
            ts = pc.get("term_structure", {}).get("severe", {})
            spreads = ts.get("prs_spread_bps", [])
            if len(spreads) >= 5:
                stats[zone]["spreads"].append(spreads[4])
            stats[zone]["elevations"].append(pc.get("elevation_m", 0))
        return stats

    def test_zone_3b_has_higher_avg_flood_count_than_zone_1(self):
        """Zone 3b properties should flood more than Zone 1 on average.

        Skips when either zone has fewer than 3 properties — with very
        small portfolios (e.g. --num-properties 20), one or both zones
        may have n=1 and any single outcome dominates the average,
        making the inequality meaningless.
        """
        stats = self._zone_stats()
        if "Zone 3b" not in stats or "Zone 1" not in stats:
            pytest.skip("Need both Zone 3b and Zone 1 properties")
        min_n = 3
        if len(stats["Zone 3b"]["flood_counts"]) < min_n or len(stats["Zone 1"]["flood_counts"]) < min_n:
            pytest.skip(
                f"Need >= {min_n} properties per zone "
                f"(have 3b={len(stats['Zone 3b']['flood_counts'])}, "
                f"1={len(stats['Zone 1']['flood_counts'])})"
            )
        avg_3b = sum(stats["Zone 3b"]["flood_counts"]) / len(stats["Zone 3b"]["flood_counts"])
        avg_1 = sum(stats["Zone 1"]["flood_counts"]) / len(stats["Zone 1"]["flood_counts"])
        assert avg_3b > avg_1, (
            f"Zone 3b avg flood count ({avg_3b:.1f}) should exceed "
            f"Zone 1 ({avg_1:.1f})"
        )

    def test_zone_3b_has_higher_avg_spread_than_zone_1(self):
        """Zone 3b properties should have higher spreads than Zone 1 on average."""
        stats = self._zone_stats()
        if "Zone 3b" not in stats or "Zone 1" not in stats:
            pytest.skip("Need both Zone 3b and Zone 1 properties")
        if not stats["Zone 3b"]["spreads"] or not stats["Zone 1"]["spreads"]:
            pytest.skip("No spread data for both zones")
        min_n = 3
        if len(stats["Zone 3b"]["spreads"]) < min_n or len(stats["Zone 1"]["spreads"]) < min_n:
            pytest.skip(
                f"Need >= {min_n} properties per zone "
                f"(have 3b={len(stats['Zone 3b']['spreads'])}, "
                f"1={len(stats['Zone 1']['spreads'])})"
            )
        avg_3b = sum(stats["Zone 3b"]["spreads"]) / len(stats["Zone 3b"]["spreads"])
        avg_1 = sum(stats["Zone 1"]["spreads"]) / len(stats["Zone 1"]["spreads"])
        assert avg_3b > avg_1, (
            f"Zone 3b avg spread ({avg_3b:.1f}bp) should exceed "
            f"Zone 1 ({avg_1:.1f}bp)"
        )

    def _zone_offset_stats(self):
        """Collect per-zone vertical offset (elevation above synthetic gauge)."""
        data = _propertyhc()
        curves = data.get("property_hazard_curves", {})
        stats = {}
        for prop_id, pc in curves.items():
            zone = pc.get("flood_zone", "Unknown")
            if zone not in stats:
                stats[zone] = []
            # Compute offset above the synthetic gauge (controlling boundary)
            prop_elev = pc.get("elevation_m", 0)
            ngs = pc.get("nearest_gauges", [])
            synth = next((ng for ng in ngs if ng.get("gauge_id", "").startswith("SYNTH")), None)
            if synth:
                gauge_elev = synth.get("gauge_elevation_m", prop_elev)
                offset = prop_elev - gauge_elev
                stats[zone].append(offset)
        return stats

    def test_zone_3b_lower_avg_offset_than_zone_1(self):
        """Zone 3b properties should be closer to gauge level than Zone 1."""
        offsets = self._zone_offset_stats()
        if "Zone 3b" not in offsets or "Zone 1" not in offsets:
            pytest.skip("Need both Zone 3b and Zone 1 properties")
        avg_3b = sum(offsets["Zone 3b"]) / len(offsets["Zone 3b"])
        avg_1 = sum(offsets["Zone 1"]) / len(offsets["Zone 1"])
        assert avg_3b < avg_1, (
            f"Zone 3b avg offset ({avg_3b:.2f}m) should be lower than "
            f"Zone 1 ({avg_1:.2f}m)"
        )

    def test_zone_offset_ordering(self):
        """Average offset above gauge should increase from Zone 3b → 3a → 2 → 1."""
        offsets = self._zone_offset_stats()
        zone_order = ["Zone 3b", "Zone 3a", "Zone 2", "Zone 1"]
        avgs = {}
        for z in zone_order:
            if z in offsets and offsets[z]:
                avgs[z] = sum(offsets[z]) / len(offsets[z])
        present = [z for z in zone_order if z in avgs]
        if len(present) < 2:
            pytest.skip("Need at least 2 zones with data")
        for i in range(len(present) - 1):
            assert avgs[present[i]] <= avgs[present[i + 1]], (
                f"Offset ordering violated: {present[i]}={avgs[present[i]]:.2f}m "
                f"> {present[i+1]}={avgs[present[i+1]]:.2f}m"
            )

    def test_all_four_zones_represented(self):
        """All four EA flood zones should appear in the portfolio."""
        stats = self._zone_stats()
        for zone in ["Zone 3b", "Zone 3a", "Zone 2", "Zone 1"]:
            assert zone in stats and len(stats[zone]["flood_counts"]) > 0, (
                f"{zone} not represented in portfolio"
            )

    def test_spread_ordering_by_zone(self):
        """Average spreads should decrease from Zone 3b → 3a → 2 → 1.

        Only includes zones with >= 3 properties so a single low-flood
        outlier in a 1-property zone doesn't break the ordering.
        """
        stats = self._zone_stats()
        zone_order = ["Zone 3b", "Zone 3a", "Zone 2", "Zone 1"]
        min_n = 3
        avgs = {}
        for z in zone_order:
            if z in stats and len(stats[z]["spreads"]) >= min_n:
                avgs[z] = sum(stats[z]["spreads"]) / len(stats[z]["spreads"])
        present = [z for z in zone_order if z in avgs]
        if len(present) < 2:
            pytest.skip(f"Need at least 2 zones with >= {min_n} properties of spread data")
        for i in range(len(present) - 1):
            assert avgs[present[i]] >= avgs[present[i + 1]], (
                f"Spread ordering violated: {present[i]}={avgs[present[i]]:.1f}bp "
                f"< {present[i+1]}={avgs[present[i+1]]:.1f}bp"
            )


class TestSyntheticGaugeConsistency:
    """Verify synthetic gauge is the controlling gauge in propertyhc."""

    def test_synthetic_is_first_nearest_gauge(self):
        """Every property should have a synthetic gauge at position [0]."""
        data = _propertyhc()
        curves = data.get("property_hazard_curves", {})
        for prop_id, pc in curves.items():
            ngs = pc.get("nearest_gauges", [])
            if not ngs:
                continue
            first = ngs[0].get("gauge_id", "")
            assert first.startswith("SYNTH"), (
                f"{prop_id} first gauge is {first}, expected SYNTH-*"
            )

    def test_zone_consistent_with_synthetic_offset(self):
        """Zone must match the elevation offset above the synthetic gauge."""
        from config.port import EA_FLOOD_ZONE_ELEVATION_BOUNDS
        data = _propertyhc()
        curves = data.get("property_hazard_curves", {})
        for prop_id, pc in curves.items():
            zone = pc.get("flood_zone", "Zone 1")
            ngs = pc.get("nearest_gauges", [])
            synth = next((ng for ng in ngs if ng["gauge_id"].startswith("SYNTH")), None)
            if not synth:
                continue
            offset = pc["elevation_m"] - synth["gauge_elevation_m"]
            lo, hi = EA_FLOOD_ZONE_ELEVATION_BOUNDS.get(zone, (0, None))
            if hi is None:
                assert offset >= lo, (
                    f"{prop_id} zone={zone} but offset={offset:.2f}m (expected >= {lo})"
                )
            else:
                assert lo <= offset < hi, (
                    f"{prop_id} zone={zone} but offset={offset:.2f}m "
                    f"(expected [{lo}, {hi}))"
                )
