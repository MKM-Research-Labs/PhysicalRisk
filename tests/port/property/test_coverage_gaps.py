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
Tests targeting uncovered lines in generator.py and locations.py.

generator.py  189-191  Exception during JSON save
generator.py  229      generate_properties() with catchment_id
locations.py  34       _zone_from_offset fallback return 'Zone 1'
locations.py  63-66    area_value_factors = {} when neither attr exists
locations.py  108-109  seg_a/seg_b fallback when no gauge_points
locations.py  154      _load_synthetic_gauges returns [] when output_dir is None
locations.py  350      _ensure_off_river returns early when norm < 1e-12
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

import database
from port.src.property.main import PropertyPortfolioGenerator
from port.src.property.main.locations import _zone_from_offset
from db_helpers import tmp_catchment

from .conftest import GAUGE_POINTS, make_portfolio_gen, make_portfolio_params


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") for every test in this module.

    The migrated property generator/locations mixin read the gauge portfolio and write
    properties through ``database``; rooting the backend at ``tmp_path`` isolates those
    and lets a test pre-write ``tmp_path / 'gauge.json'`` for the synthetic-gauge path."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# locations.py line 34 -- _zone_from_offset fallback
# ===========================================================================

class TestZoneFromOffsetBelowRiver:

    def test_negative_offset_returns_zone_3b(self):
        """A below-river property is functional floodplain (Zone 3b), whose
        lower bound is unbounded — not the lowest-risk Zone 1."""
        assert _zone_from_offset(-1.0) == 'Zone 3b'

    def test_very_large_negative_offset_returns_zone_3b(self):
        assert _zone_from_offset(-100.0) == 'Zone 3b'


# ===========================================================================
# locations.py lines 63-66 -- no AREA_VALUE_FACTORS or AREAVALUEFACTORS
# ===========================================================================

class TestNoAreaValueFactors:

    def test_generate_locations_with_no_area_value_factors(self, tmp_path):
        """When params has neither AREA_VALUE_FACTORS nor AREAVALUEFACTORS,
        area_value_factors defaults to {}."""
        params = MagicMock()
        params.AREAS = ["A", "B"]
        del params.AREA_VALUE_FACTORS
        del params.AREAVALUEFACTORS
        params.STREETS = {}
        params.CENTER_LAT = 51.5
        params.CENTER_LON = -0.1
        params.GAUGE_POINTS = None
        del params.GAUGEPOINTS
        params.get_elevation = MagicMock(return_value=8.0)

        gen = PropertyPortfolioGenerator(
            verbose=False, catchment_params=params)
        locs = gen._generate_locations(3)
        assert len(locs) == 3
        # value_factor should default to 1.0 when area not in empty dict
        for loc in locs:
            assert loc["value_factor"] == 1.0


# ===========================================================================
# locations.py lines 108-109 -- seg_a/seg_b fallback (no gauge_points)
# ===========================================================================

class TestSegFallbackNoGaugePoints:

    def test_synthetics_with_no_gauge_points_uses_delta_fallback(self, tmp_path):
        """When synthetics exist but gauge_points is empty/None, the code
        falls back to seg_a/seg_b computed from a small lat delta."""
        params = MagicMock()
        params.AREAS = ["A"]
        params.AREA_VALUE_FACTORS = {"A": 1.0}
        params.STREETS = {}
        params.CENTER_LAT = 51.5
        params.CENTER_LON = -0.1
        params.GAUGE_POINTS = None
        del params.GAUGEPOINTS
        params.get_elevation = MagicMock(return_value=8.0)

        gen = PropertyPortfolioGenerator(
            verbose=False, catchment_params=params)

        # Write a gauge.json with synthetic gauges so the synthetics branch runs
        gauge_data = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {"GaugeID": "SYN-001"},
                        "Location": {
                            "LatitudeDegrees": 51.5,
                            "LongitudeDegrees": -0.1,
                            "Elevation": 5.0,
                        },
                    }
                }
            ]
        }
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

        locs = gen._generate_locations(2)
        assert len(locs) == 2

    def test_synthetics_with_single_gauge_point(self, tmp_path):
        """gauge_points with only 1 element also triggers the fallback."""
        params = MagicMock()
        params.AREAS = ["A"]
        params.AREA_VALUE_FACTORS = {"A": 1.0}
        params.STREETS = {}
        params.CENTER_LAT = 51.5
        params.CENTER_LON = -0.1
        params.GAUGE_POINTS = [(51.5, -0.1, 5.0)]
        del params.GAUGEPOINTS
        params.get_elevation = MagicMock(return_value=8.0)

        gen = PropertyPortfolioGenerator(
            verbose=False, catchment_params=params)

        gauge_data = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {"GaugeID": "SYN-001"},
                        "Location": {
                            "LatitudeDegrees": 51.5,
                            "LongitudeDegrees": -0.1,
                            "Elevation": 5.0,
                        },
                    }
                }
            ]
        }
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

        locs = gen._generate_locations(2)
        assert len(locs) == 2


# ===========================================================================
# locations.py -- _load_synthetic_gauges returns [] when no gauge portfolio
# ===========================================================================

class TestLoadSyntheticGaugesNoPortfolio:

    def test_returns_empty_when_no_gauge_portfolio(self, tmp_path):
        """With no gauge portfolio persisted for the catchment, returns []."""
        gen = make_portfolio_gen(tmp_path)
        # The autouse tmp_catchment backend is empty (no gauge.json written).
        result = gen._load_synthetic_gauges()
        assert result == []


# ===========================================================================
# locations.py line 350 -- _ensure_off_river with zero-length segment
# ===========================================================================

class TestEnsureOffRiverZeroLengthSegment:

    def test_zero_length_segment_returns_original_coords(self, tmp_path):
        """When all gauge points are the same, the perpendicular norm is ~0,
        so _ensure_off_river returns (lat, lon) unchanged."""
        gen = make_portfolio_gen(tmp_path)
        # Two identical gauge points => seg_lat=0, seg_lon=0 => norm=0
        same_point = [(51.5, -0.1, 5.0), (51.5, -0.1, 5.0)]
        # The point must be close to the segment to get past the
        # best_dist >= MIN_RIVER_DISTANCE_M check
        lat, lon = 51.5, -0.1
        result_lat, result_lon = gen._ensure_off_river(lat, lon, same_point)
        assert result_lat == lat
        assert result_lon == lon


# ===========================================================================
# generator.py -- exception during the database save is logged and re-raised
# ===========================================================================

class TestGeneratorSaveError:

    def test_save_exception_is_logged_and_reraised(self, tmp_path):
        """A failure in database.save_properties propagates out of generate()."""
        gen = make_portfolio_gen(tmp_path)
        with patch('database.save_properties', side_effect=OSError("Simulated write failure")):
            with pytest.raises(OSError, match="Simulated write failure"):
                gen.generate(count=2)


# ===========================================================================
# (generate_properties no longer accepts catchment_id — catchment is
# pinned globally via config.catchment_id by the CLI entry point.)
