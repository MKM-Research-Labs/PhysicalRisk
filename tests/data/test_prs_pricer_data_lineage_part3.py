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
Data lineage tests for the property PRS pricer (part 3).

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
