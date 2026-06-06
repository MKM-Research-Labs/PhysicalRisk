# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Property time series cross-references and data quality (part 2)."""

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
