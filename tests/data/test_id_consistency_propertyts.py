# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Property time series cross-references and data quality."""

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
    THAMES_LAT_BOUNDS,
    THAMES_LON_BOUNDS,
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
            "Regenerate: python app.py port --propertyts"
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
            if not (THAMES_LAT_BOUNDS[0] <= lat <= THAMES_LAT_BOUNDS[1]):
                bad.append(f"{pid} lat={lat}")
            elif not (THAMES_LON_BOUNDS[0] <= lon <= THAMES_LON_BOUNDS[1]):
                bad.append(f"{pid} lon={lon}")
        assert len(bad) == 0, (
            f"{len(bad)} propertyts files have out-of-bounds coords: "
            f"{bad[:5]}. Expected lat {THAMES_LAT_BOUNDS}, "
            f"lon {THAMES_LON_BOUNDS}."
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


# =========================================================================
# Property TS variants (TSD / TSE)
# =========================================================================

class TestPropertyTSVariants:
    """propertytsd/ and propertytse/ must mirror propertyts/."""

    def _variant_dir(self, variant):
        return INPUT_DIR / variant

    def test_propertytsd_count_matches(self):
        """propertytsd/ must have the same number of files as propertyts/."""
        pts_dir = INPUT_DIR / "propertyts"
        tsd_dir = self._variant_dir("propertytsd")
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        if not tsd_dir.exists():
            pytest.skip("propertytsd/ not generated yet")
        pts_count = len(list(pts_dir.glob("PROP-*.json")))
        tsd_count = len(list(tsd_dir.glob("PROP-*.json")))
        assert tsd_count == pts_count, (
            f"propertytsd/ has {tsd_count} files but propertyts/ has "
            f"{pts_count}. Regenerate: python app.py port --propertyts"
        )

    def test_propertytse_count_matches(self):
        """propertytse/ must have the same number of files as propertyts/."""
        pts_dir = INPUT_DIR / "propertyts"
        tse_dir = self._variant_dir("propertytse")
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        if not tse_dir.exists():
            pytest.skip("propertytse/ not generated yet")
        pts_count = len(list(pts_dir.glob("PROP-*.json")))
        tse_count = len(list(tse_dir.glob("PROP-*.json")))
        assert tse_count == pts_count, (
            f"propertytse/ has {tse_count} files but propertyts/ has "
            f"{pts_count}. Regenerate: python app.py port --propertyts"
        )

    def test_propertytsd_ids_match(self):
        """propertytsd/ property IDs must match propertyts/ (sampled)."""
        pts_dir = INPUT_DIR / "propertyts"
        tsd_dir = self._variant_dir("propertytsd")
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        if not tsd_dir.exists():
            pytest.skip("propertytsd/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        missing = []
        for f in sample:
            tsd_file = tsd_dir / f.name
            if not tsd_file.exists():
                missing.append(f.name)
        assert len(missing) == 0, (
            f"{len(missing)} propertyts files missing from propertytsd/: "
            f"{missing[:5]}"
        )

    def test_propertytse_ids_match(self):
        """propertytse/ property IDs must match propertyts/ (sampled)."""
        pts_dir = INPUT_DIR / "propertyts"
        tse_dir = self._variant_dir("propertytse")
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        if not tse_dir.exists():
            pytest.skip("propertytse/ not generated yet")
        sample = _sample_files(pts_dir)
        if not sample:
            pytest.skip("No propertyts files found")
        missing = []
        for f in sample:
            tse_file = tse_dir / f.name
            if not tse_file.exists():
                missing.append(f.name)
        assert len(missing) == 0, (
            f"{len(missing)} propertyts files missing from propertytse/: "
            f"{missing[:5]}"
        )

    def test_propertytsd_nearest_gauges_present(self):
        """propertytsd/ files must have nearest_gauges field."""
        tsd_dir = self._variant_dir("propertytsd")
        if not tsd_dir.exists():
            pytest.skip("propertytsd/ not generated yet")
        sample = _sample_files(tsd_dir)
        if not sample:
            pytest.skip("No propertytsd files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            if not d.get("nearest_gauges"):
                bad.append(pid)
        assert len(bad) == 0, (
            f"{len(bad)} propertytsd files lack nearest_gauges: {bad[:5]}"
        )

    def test_propertytse_nearest_gauges_present(self):
        """propertytse/ files must have nearest_gauges field."""
        tse_dir = self._variant_dir("propertytse")
        if not tse_dir.exists():
            pytest.skip("propertytse/ not generated yet")
        sample = _sample_files(tse_dir)
        if not sample:
            pytest.skip("No propertytse files found")
        bad = []
        for f in sample:
            d = _load_ts_record(f)
            pid = d.get("property_id", f.name)
            if not d.get("nearest_gauges"):
                bad.append(pid)
        assert len(bad) == 0, (
            f"{len(bad)} propertytse files lack nearest_gauges: {bad[:5]}"
        )
