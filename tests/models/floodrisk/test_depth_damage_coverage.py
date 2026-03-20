# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Coverage-expansion tests for models.floodrisk.depth_damage.

Targets uncovered lines: 50-57 (calculate_flood_depths non-None path),
69-98 (calculate_synthetic_flood_depths flooding + distance branches),
122 (scalar_depth_damage fallback), 140-165 (depth_damage_function).
"""

import pytest
import numpy as np

try:
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

from models.floodrisk.depth_damage import scalar_depth_damage


# ---------------------------------------------------------------------------
# scalar_depth_damage — final fallback (line 122)
# ---------------------------------------------------------------------------

class TestScalarDepthDamageFallback:
    """Line 122 is a defensive return 0.0 at the end of the loop.
    It is technically unreachable with well-formed DEPTH_POINTS, but we
    can verify the function handles edge-case depths near control points."""

    def test_just_below_first_positive_depth(self):
        """Very small positive depth (between 0 and first control point)."""
        d = scalar_depth_damage(0.001)
        assert 0.0 < d < 0.05

    def test_at_each_control_point(self):
        """Every control point must return a value in [0, 1]."""
        from config.models import DEPTH_POINTS
        for dp in DEPTH_POINTS:
            val = scalar_depth_damage(dp)
            assert 0.0 <= val <= 1.0


# ---------------------------------------------------------------------------
# calculate_flood_depths — non-None gauge_data (lines 50-57)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestCalculateFloodDepthsNonNone:

    @pytest.fixture
    def properties_near_thames(self):
        """Properties close to Thames (51.5, -0.1) with low elevation."""
        n = 3
        geometry = [
            Point(-0.1, 51.5),   # right on Thames centre
            Point(-0.05, 51.51), # close
            Point(0.0, 51.52),   # a bit further
        ]
        return gpd.GeoDataFrame(
            {'property_id': [f'P{i}' for i in range(n)],
             'elevation': [2.0, 3.0, 4.0]},
            geometry=geometry, crs='EPSG:4326',
        )

    def test_with_gauge_data_delegates_to_synthetic(self, properties_near_thames):
        """Lines 50-57: non-None gauge_data calls calculate_synthetic_flood_depths."""
        from models.floodrisk.depth_damage import calculate_flood_depths
        gauge_data = pd.DataFrame({
            'water_level': [6.0, 5.8],
            'severe_level': [5.0, 5.0],
        })
        depths = calculate_flood_depths(properties_near_thames, gauge_data)
        assert len(depths) == 3
        assert isinstance(depths, np.ndarray)


# ---------------------------------------------------------------------------
# calculate_synthetic_flood_depths — all branches (lines 69-98)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestSyntheticFloodDepths:

    @pytest.fixture
    def properties_near_thames(self):
        geometry = [
            Point(-0.1, 51.5),    # ~0 km from Thames centre
            Point(-0.05, 51.505), # close
        ]
        return gpd.GeoDataFrame(
            {'property_id': ['P0', 'P1'], 'elevation': [2.0, 3.0]},
            geometry=geometry, crs='EPSG:4326',
        )

    @pytest.fixture
    def properties_far_away(self):
        """Properties far from Thames (>25km) — should get zero depth."""
        geometry = [
            Point(1.0, 52.0),  # far east and north
        ]
        return gpd.GeoDataFrame(
            {'property_id': ['PFAR'], 'elevation': [2.0]},
            geometry=geometry, crs='EPSG:4326',
        )

    def test_flooding_path_produces_positive_depths(self, properties_near_thames):
        """Lines 72-96: water_level > severe_level, close to Thames."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        gauge_data = pd.DataFrame({
            'water_level': [7.0, 6.5],
            'severe_level': [5.0, 5.0],
        })
        depths = calculate_synthetic_flood_depths(properties_near_thames, gauge_data)
        # Properties close to Thames with low elevation should flood
        assert np.any(depths > 0), f"Expected some flooding, got {depths}"

    def test_depths_capped_at_5m(self, properties_near_thames):
        """Line 96: flood_depths[i] = min(depth, 5.0)."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        gauge_data = pd.DataFrame({
            'water_level': [100.0],  # extreme water level
            'severe_level': [5.0],
        })
        depths = calculate_synthetic_flood_depths(properties_near_thames, gauge_data)
        assert np.all(depths <= 5.0)

    def test_far_away_property_gets_zero(self, properties_far_away):
        """Lines 93-94: distance >= max_distance → depth = 0.0."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        gauge_data = pd.DataFrame({
            'water_level': [7.0],
            'severe_level': [5.0],
        })
        depths = calculate_synthetic_flood_depths(properties_far_away, gauge_data)
        assert depths[0] == 0.0

    def test_below_severe_returns_zeros(self, properties_near_thames):
        """Lines 72-76: water_level <= severe_level → no flooding."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        gauge_data = pd.DataFrame({
            'water_level': [3.0],
            'severe_level': [5.0],
        })
        depths = calculate_synthetic_flood_depths(properties_near_thames, gauge_data)
        np.testing.assert_allclose(depths, 0.0)

    def test_none_gauge_returns_zeros(self, properties_near_thames):
        """Lines 72: gauge_data is None."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        depths = calculate_synthetic_flood_depths(properties_near_thames, None)
        np.testing.assert_allclose(depths, 0.0)

    def test_empty_gauge_returns_zeros(self, properties_near_thames):
        """Lines 72: len(gauge_data) == 0."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        empty = pd.DataFrame({'water_level': [], 'severe_level': []})
        depths = calculate_synthetic_flood_depths(properties_near_thames, empty)
        np.testing.assert_allclose(depths, 0.0)

    def test_distance_factor_applied(self, properties_near_thames):
        """Lines 89-92: distance_factor reduces depth proportionally."""
        from models.floodrisk.depth_damage import calculate_synthetic_flood_depths
        gauge_data = pd.DataFrame({
            'water_level': [7.0],
            'severe_level': [5.0],
        })
        depths = calculate_synthetic_flood_depths(properties_near_thames, gauge_data)
        # Both should be positive (close to Thames)
        # First property is right at Thames centre, second slightly further
        assert depths[0] > 0
        assert depths[1] > 0


# ---------------------------------------------------------------------------
# depth_damage_function — all property types + floor levels (lines 140-165)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_GEO, reason="geopandas not installed")
class TestDepthDamageFunctionCoverage:

    @pytest.fixture
    def properties(self):
        n = 5
        lons = np.linspace(-0.3, 0.1, n)
        lats = np.linspace(51.4, 51.6, n)
        geometry = [Point(lon, lat) for lon, lat in zip(lons, lats)]
        return gpd.GeoDataFrame(
            {
                'property_id': [f'PROP-{i:03d}' for i in range(n)],
                'value': [300_000] * n,
                'property_type': ['residential', 'commercial', 'industrial',
                                  'residential', 'other'],
                'floor_level_metres': [0.0, 0.0, 0.0, 0.5, 0.0],
            },
            geometry=geometry,
            crs='EPSG:4326',
        )

    def test_full_function_returns_correct_length(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.array([0.5, 1.0, 1.5, 2.0, 3.0])
        result = depth_damage_function(depths, properties)
        assert len(result) == len(properties)

    def test_commercial_gets_1_2x_factor(self, properties):
        """Line 150: commercial factor = 1.2."""
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.full(len(properties), 2.0)
        result = depth_damage_function(depths, properties)
        # commercial (index 1) should have higher damage than residential (index 0)
        assert result[1] > result[0]

    def test_industrial_gets_0_9x_factor(self, properties):
        """Line 151: industrial factor = 0.9."""
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.full(len(properties), 2.0)
        result = depth_damage_function(depths, properties)
        # industrial (index 2) should have lower damage than residential (index 0)
        assert result[2] < result[0]

    def test_unknown_type_defaults_to_1_0(self, properties):
        """Line 155: .get(str(pt).lower(), 1.0) — 'other' defaults to 1.0."""
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.full(len(properties), 2.0)
        result = depth_damage_function(depths, properties)
        # 'other' (index 4, floor=0) should equal residential (index 0, floor=0)
        assert result[4] == pytest.approx(result[0])

    def test_floor_level_adjustment(self, properties):
        """Lines 159-160: adjusted_depths = max(depths - floor_levels, 0)."""
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.array([0.3, 0.3, 0.3, 0.3, 0.3])
        result = depth_damage_function(depths, properties)
        # Index 3 has floor_level_metres=0.5, effective depth = max(0.3-0.5,0) = 0 → no damage
        assert result[3] == pytest.approx(0.0)

    def test_output_clipped_to_unit_interval(self, properties):
        """Line 165: np.clip(final_damage, 0, 1)."""
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
        result = depth_damage_function(depths, properties)
        assert np.all(result <= 1.0)
        assert np.all(result >= 0.0)

    def test_zero_depths_all_zero(self, properties):
        from models.floodrisk.depth_damage import depth_damage_function
        depths = np.zeros(len(properties))
        result = depth_damage_function(depths, properties)
        np.testing.assert_allclose(result, 0.0)
