# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for synthetic distance timeseries (propertytsd / mode="shd").

In shd mode, the property elevation is set to the gauge elevation
(zero elevation differential), so flood thresholds are lower and more
properties should flood.
"""

import json

import pytest

from port.src.property.ts import PropertyTimeSeriesGenerator

from .conftest import (
    make_gauge_lookup,
    make_gaugets,
    make_prop,
)


@pytest.fixture
def shd_setup(tmp_path):
    """Set up a generator in shd mode with basic property/gauge data."""
    gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="shd")
    return gen, tmp_path


class TestShdOutputDirectory:

    def test_shd_writes_to_propertytsd_dir(self, shd_setup, tmp_path):
        """Mode shd should write PROP-*.json into propertytsd/ not propertyts/."""
        gen, _ = shd_setup
        assert gen._MODE_DIRS["shd"] == "propertytsd"

    def test_she_writes_to_propertytse_dir(self, tmp_path):
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="she")
        assert gen._MODE_DIRS["she"] == "propertytse"


class TestShdFloodMixin:

    def test_shd_sets_effective_elevation_to_gauge(self, tmp_path):
        """In shd mode the property elevation should match the gauge,
        yielding height_diff = 0 in the flood event."""
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="shd")
        gauge_lookup = make_gauge_lookup("GAUGE-001", elevation=3.0)
        gaugets = make_gaugets("GAUGE-001", peak_level=5.5)

        # Property at elevation 8.0 (5m above gauge)
        prop = make_prop("PROP-SHD1", elevation=8.0)
        pts_dir = tmp_path / "propertytsd"
        pts_dir.mkdir(parents=True)

        result = gen._process_property(prop, gauge_lookup, gaugets, pts_dir, mode="shd")
        assert result is not None

        # Read the written file and verify elevation was overridden
        prop_file = pts_dir / "PROP-SHD1.json"
        data = json.loads(prop_file.read_text())

        # In shd mode, effective elevation should be gauge elevation (3.0),
        # but sanity check lifts it to gauge + 0.5 = 3.5
        assert data["elevation_m"] <= 4.0  # much less than original 8.0

    def test_she_sets_distance_to_zero(self, tmp_path):
        """In she mode all gauge distances should be 0."""
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="she")
        gauge_lookup = make_gauge_lookup("GAUGE-001", elevation=3.0)
        gaugets = make_gaugets("GAUGE-001", peak_level=5.5)

        prop = make_prop("PROP-SHE1", elevation=5.0)
        pts_dir = tmp_path / "propertytse"
        pts_dir.mkdir(parents=True)

        result = gen._process_property(prop, gauge_lookup, gaugets, pts_dir, mode="she")
        assert result is not None

        prop_file = pts_dir / "PROP-SHE1.json"
        data = json.loads(prop_file.read_text())

        # All nearest gauge distances should be 0
        for ng in data["nearest_gauges"]:
            assert ng["distance_m"] == 0.0
