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
Tests for the BRI-adjusted floor timeseries (propertytsb / mode="bri").

In "bri" mode the flood threshold is raised from the surveyed
FloorLevelMeters to Construction.BRIAdjustedFloorLevelMeters (the
Building Resilience Index floor credit). Distance and elevation are
untouched — only the floor side of the flood test moves — so a resilient
building floods at a higher water level and counts fewer / shallower
floods. When the adjusted field is absent, the mode falls back to the
surveyed floor and is a no-op.
"""

import json

import pytest

from port.src.property.ts import PropertyTimeSeriesGenerator

from .conftest import make_gauge_lookup, make_gaugets, make_prop


def _prop_with_bri(prop_id, elevation, floor_level, bri_floor):
    """make_prop + an injected BRIAdjustedFloorLevelMeters."""
    prop = make_prop(prop_id, elevation=elevation, floor_level=floor_level)
    prop["PropertyHeader"]["Construction"]["BRIAdjustedFloorLevelMeters"] = bri_floor
    return prop


def _run(gen, prop, tmp_path, subdir, mode):
    pts_dir = tmp_path / subdir
    pts_dir.mkdir(parents=True, exist_ok=True)
    result = gen._process_property(prop, make_gauge_lookup("GAUGE-001", elevation=3.0),
                                   make_gaugets("GAUGE-001", peak_level=5.8),
                                   pts_dir, mode=mode)
    assert result is not None
    return json.loads((pts_dir / f"{prop['PropertyHeader']['Header']['PropertyID']}.json").read_text())


class TestBriOutputDirectory:
    def test_bri_ts_dir(self, tmp_path):
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="bri")
        assert gen.ASSET_CONFIG.ts_dirs["bri"] == "propertytsb"

    def test_bri_hc_file(self, tmp_path):
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="bri")
        assert gen.ASSET_CONFIG.hc_files["bri"] == "propertybri.json"


class TestBriFloorSelection:
    def test_bri_uses_adjusted_floor(self, tmp_path):
        """The written floor_level_m reflects the BRI-adjusted floor, not the
        surveyed FloorLevelMeters."""
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="bri")
        prop = _prop_with_bri("PROP-BRI1", elevation=3.6, floor_level=0.3, bri_floor=3.0)
        data = _run(gen, prop, tmp_path, "propertytsb", "bri")
        assert data["floor_level_m"] == pytest.approx(3.0)

    def test_normal_uses_surveyed_floor(self, tmp_path):
        """In normal mode the same record keeps the surveyed floor."""
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="normal")
        prop = _prop_with_bri("PROP-BRI1", elevation=3.6, floor_level=0.3, bri_floor=3.0)
        data = _run(gen, prop, tmp_path, "propertyts", "normal")
        assert data["floor_level_m"] == pytest.approx(0.3)

    def test_bri_fallback_without_field(self, tmp_path):
        """No BRIAdjustedFloorLevelMeters → bri mode falls back to the surveyed
        floor (safe no-op)."""
        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="bri")
        prop = make_prop("PROP-BRI2", elevation=3.6, floor_level=0.3)  # no BRI field
        data = _run(gen, prop, tmp_path, "propertytsb", "bri")
        assert data["floor_level_m"] == pytest.approx(0.3)


class TestBriReducesFlooding:
    def test_bri_depth_not_greater_than_normal(self, tmp_path):
        """Raising the floor can only reduce (never increase) flood depth."""
        gen_n = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="normal")
        gen_b = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="bri")
        prop = _prop_with_bri("PROP-BRI3", elevation=3.6, floor_level=0.1, bri_floor=4.0)

        d_normal = _run(gen_n, prop, tmp_path, "propertyts", "normal")
        d_bri = _run(gen_b, prop, tmp_path, "propertytsb", "bri")

        max_n = max((e["flood_depth_m"] for e in d_normal["flood_events"]), default=0.0)
        max_b = max((e["flood_depth_m"] for e in d_bri["flood_events"]), default=0.0)
        assert max_b <= max_n

    def test_high_bri_floor_suppresses_flood(self, tmp_path):
        """A floor raised well above the water surface zeroes the flood depth
        that the surveyed floor would have registered."""
        gen_n = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="normal")
        gen_b = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False, mode="bri")
        # Low floor floods in normal mode; a 10m BRI floor is above any water.
        prop = _prop_with_bri("PROP-BRI4", elevation=3.5, floor_level=0.1, bri_floor=10.0)

        d_normal = _run(gen_n, prop, tmp_path, "propertyts", "normal")
        d_bri = _run(gen_b, prop, tmp_path, "propertytsb", "bri")

        floods_n = sum(1 for e in d_normal["flood_events"] if e.get("flooded"))
        floods_b = sum(1 for e in d_bri["flood_events"] if e.get("flooded"))
        assert floods_n >= 1          # normal mode floods
        assert floods_b == 0          # BRI floor suppresses it
