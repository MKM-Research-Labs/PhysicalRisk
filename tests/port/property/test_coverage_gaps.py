# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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

from port.src.property.main import PropertyPortfolioGenerator
from port.src.property.main.locations import _zone_from_offset

from .conftest import GAUGE_POINTS, make_portfolio_gen, make_portfolio_params


# ===========================================================================
# locations.py line 34 -- _zone_from_offset fallback
# ===========================================================================

class TestZoneFromOffsetFallback:

    def test_negative_offset_returns_zone_1(self):
        """A negative offset doesn't match any (lo, hi) range, so
        the loop falls through and the function returns 'Zone 1'."""
        assert _zone_from_offset(-1.0) == 'Zone 1'

    def test_very_large_negative_offset_returns_zone_1(self):
        assert _zone_from_offset(-100.0) == 'Zone 1'


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
            output_dir=tmp_path, verbose=False, catchment_params=params)
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
            output_dir=tmp_path, verbose=False, catchment_params=params)

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
            output_dir=tmp_path, verbose=False, catchment_params=params)

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
# locations.py line 154 -- _load_synthetic_gauges returns [] when no output_dir
# ===========================================================================

class TestLoadSyntheticGaugesNoOutputDir:

    def test_returns_empty_when_output_dir_is_none(self, tmp_path):
        """When output_dir is None, _load_synthetic_gauges returns []."""
        gen = make_portfolio_gen(tmp_path)
        # Force output_dir to None after construction (constructor defaults it)
        gen.output_dir = None
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
# generator.py lines 189-191 -- exception during JSON save
# ===========================================================================

class TestGeneratorJsonSaveError:

    def test_json_save_exception_is_logged_and_reraised(self, tmp_path):
        """Force an exception during json.dump and verify it's re-raised."""
        gen = make_portfolio_gen(tmp_path)

        # Make the output directory read-only so the file write fails
        output_dir = tmp_path / "readonly_out"
        output_dir.mkdir()
        gen.output_dir = output_dir

        # Patch open to raise an OSError when writing
        original_open = open

        def failing_open(path, mode='r', *args, **kwargs):
            if 'w' in str(mode) and 'property.json' in str(path):
                raise OSError("Simulated write failure")
            return original_open(path, mode, *args, **kwargs)

        with patch('builtins.open', side_effect=failing_open):
            with pytest.raises(OSError, match="Simulated write failure"):
                gen.generate(count=2)


# ===========================================================================
# generator.py line 229 -- generate_properties with catchment_id
# ===========================================================================

class TestGeneratePropertiesConvenience:

    def test_catchment_id_sets_config(self, tmp_path):
        """Calling generate_properties(catchment_id='THAMES') sets
        config.CATCHMENT to 'thames'."""
        from port.src.property.main.generator import generate_properties
        from config import config

        original_catchment = config.CATCHMENT

        try:
            with patch.object(
                PropertyPortfolioGenerator, 'generate',
                return_value={"data": {}, "file_path": "", "processing_stats": {}}
            ):
                generate_properties(count=1, output_dir=tmp_path,
                                    catchment_id="THAMES")
                assert config.CATCHMENT == "thames"
        finally:
            config.CATCHMENT = original_catchment
