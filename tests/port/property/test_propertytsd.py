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
    """Mode → output-dir mapping now lives on ASSET_CONFIG.ts_dirs so the
    same generator class can target commercial assets via a different
    asset config. The residential mapping must keep shd → propertytsd and
    she → propertytse for backward compatibility with the report tests."""

    def test_shd_writes_to_propertytsd_dir(self, shd_setup, tmp_path):
        gen, _ = shd_setup
        assert gen.ASSET_CONFIG.ts_dirs["shd"] == "propertytsd"

    def test_she_writes_to_propertytse_dir(self, tmp_path):
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="she")
        assert gen.ASSET_CONFIG.ts_dirs["she"] == "propertytse"

    def test_normal_writes_to_propertyts_dir(self, tmp_path):
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="normal")
        assert gen.ASSET_CONFIG.ts_dirs["normal"] == "propertyts"


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
