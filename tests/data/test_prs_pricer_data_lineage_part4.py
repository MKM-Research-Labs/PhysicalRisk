"""
Data lineage tests for the property PRS pricer (part 4).

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
