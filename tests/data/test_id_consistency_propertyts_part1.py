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

"""Property time series cross-references and data quality (part 1)."""

import json
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_property_ids,
    _load_counterparty_ids,
    _load_trade_counterparty_ids,
    _load_trade_ids,
    _load_propertyhc_ids,
    _load_propertyshd_ids,
    _load_propertyshe_ids,
    CATCHMENT_LAT_BOUNDS,
    CATCHMENT_LON_BOUNDS,
)


def _sample_files(directory, pattern="PROP-*.json", n=20):
    """Return a deterministic sample of up to n files from directory."""
    files = sorted(directory.glob(pattern))
    if not files:
        return []
    step = max(1, len(files) // n)
    return files[::step][:n]


def _load_ts_record(path):
    """Load a single property time series JSON file."""
    return json.load(open(path))


# =========================================================================
# Property TS cross-references
# =========================================================================

class TestPropertyTSCrossRefs:
    """propertyts/ files must reference valid entities."""

    def test_property_id_valid(self):
        """property_id in each propertyts file must exist in property.json."""
        prop_ids = _load_property_ids()
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", "")
            if pid not in prop_ids:
                bad.append(pid or f.name)
        assert len(bad) == 0, (
            f"{len(bad)}/{len(sample)} propertyts files reference "
            f"non-existent properties: {bad[:5]}. "
            "Regenerate: python phys.py port --propertyts"
        )

    def test_nearest_gauges_exist(self):
        """nearest_gauges gauge_ids must exist in gauge.json (GAUGE- prefix)."""
        gauge_ids = _load_gauge_ids()
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            for ng in d.get("nearest_gauges", []):
                gid = ng.get("gauge_id", "")
                if gid and gid.startswith("GAUGE-") and gid not in gauge_ids:
                    bad.append(f"{d.get('property_id', f.name)}->{gid}")
        assert len(bad) == 0, (
            f"{len(bad)} nearest_gauge refs point to non-existent gauges: "
            f"{bad[:5]}. propertyts/ is stale."
        )

    def test_flood_events_have_storm_ids(self):
        """Every flood event must have a storm_id."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        missing = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            for evt in d.get("flood_events", []):
                if not evt.get("storm_id", ""):
                    missing.append(pid)
                    break
        assert len(missing) == 0, (
            f"{len(missing)} propertyts files have flood events without "
            f"storm_id: {missing[:5]}"
        )

    def test_storm_ids_prefixed(self):
        """All storm_ids must start with STORM- prefix."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            for evt in d.get("flood_events", []):
                sid = evt.get("storm_id", "")
                if sid and not sid.startswith("STORM-"):
                    bad.append(f"{pid}: {sid}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have non-STORM- storm IDs: "
            f"{bad[:5]}"
        )

    def test_sample_coverage(self):
        """Sampling must cover at least 20 files (or all if fewer)."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        all_files = sorted(pts_dir.glob("PROP-*.json"))
        sample = _sample_files(pts_dir)
        if not all_files:
            pytest.skip("No propertyts files found")
        expected = min(20, len(all_files))
        assert len(sample) >= expected, (
            f"Sample too small: {len(sample)} < {expected}"
        )


# =========================================================================
# Property TS data quality
# =========================================================================

class TestPropertyTSDataQuality:
    """Property time series values must be physically plausible."""

    def test_coords_in_bounds(self):
        """Property coordinates must fall within Thames catchment bounds."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            loc = d.get("location", {})
            lat = loc.get("lat", 0)
            lon = loc.get("lon", 0)
            if not (CATCHMENT_LAT_BOUNDS[0] <= lat <= CATCHMENT_LAT_BOUNDS[1]):
                bad.append(f"{pid} lat={lat}")
            elif not (CATCHMENT_LON_BOUNDS[0] <= lon <= CATCHMENT_LON_BOUNDS[1]):
                bad.append(f"{pid} lon={lon}")
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have out-of-bounds coords: "
            f"{bad[:5]}. Expected lat {CATCHMENT_LAT_BOUNDS}, "
            f"lon {CATCHMENT_LON_BOUNDS}."
        )

    def test_elevation_positive(self):
        """Property elevation must be > 0."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            elev = d.get("elevation_m", 0)
            if elev <= 0:
                bad.append(f"{pid}={elev}")
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have non-positive elevation: "
            f"{bad[:5]}"
        )

    def test_damage_ratio_bounded(self):
        """damage_ratio must be in [0, 1]."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            for evt in d.get("flood_events", []):
                dr = evt.get("damage_ratio", 0)
                if not (0 <= dr <= 1):
                    bad.append(f"{pid}={dr}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have out-of-range damage_ratio: "
            f"{bad[:5]}. Expected [0, 1]."
        )

    def test_flood_depth_non_negative(self):
        """flood_depth_m must be >= 0."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            for evt in d.get("flood_events", []):
                fd = evt.get("flood_depth_m", 0)
                if fd < 0:
                    bad.append(f"{pid}={fd}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have negative flood_depth_m: "
            f"{bad[:5]}"
        )

    def test_distance_positive(self):
        """nearest_gauge distance_m must be > 0."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            for ng in d.get("nearest_gauges", []):
                dist = ng.get("distance_m", 0)
                if dist <= 0:
                    bad.append(f"{pid}={dist}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have non-positive distance_m: "
            f"{bad[:5]}"
        )
