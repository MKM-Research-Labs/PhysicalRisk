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
Data lineage tests for the property PRS pricer (part 2).

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

    def test_pricing_method_is_event_frequency(self):
        """MKM-EF-001 supersedes the event-count method.

        The assertion read ``event_count`` and passed only because the
        committed portfolio predated the event-frequency wiring; a fresh
        generation writes ``event_frequency``.
        """
        _, pc = _first_property()
        assert pc.get("pricing_method") == "event_frequency"

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
