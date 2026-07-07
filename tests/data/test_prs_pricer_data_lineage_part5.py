"""
Data lineage tests for the property PRS pricer (part 5).

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
            # Bounds are half-open [lo, hi); either end may be None (unbounded).
            # Zone 3b (functional floodplain) is unbounded below (lo is None).
            lo_ok = lo is None or offset >= lo
            hi_ok = hi is None or offset < hi
            assert lo_ok and hi_ok, (
                f"{prop_id} zone={zone} but offset={offset:.2f}m "
                f"(expected [{lo}, {hi}))"
            )
