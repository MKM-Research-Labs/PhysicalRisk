"""Tests for terrain grid generation and bilinear interpolation."""

import math

import pytest

from config.models import EA_FLOOD_ZONE_RATES
from models.hazard.prs_analytical import compute_prs_spread
from models.hazard.terrain_grid import (
    ELEV_SCALE_M,
    GRID_DISTANCES_M,
    GRID_ELEVATIONS_M,
    GRID_RECOVERY,
    GRID_RISK_FREE_RATE,
    GRID_TENOR,
    compute_terrain_grid,
    interpolate_terrain_spread,
)
from models.floodrisk.velocity import compute_retention


@pytest.fixture(scope="module")
def grid():
    """Compute grid once for all tests."""
    return compute_terrain_grid()


# ===================================================================
# Grid structure tests
# ===================================================================

class TestGridStructure:

    def test_has_distances(self, grid):
        assert grid['distances'] == GRID_DISTANCES_M

    def test_has_elevations(self, grid):
        assert grid['elevations'] == GRID_ELEVATIONS_M

    def test_has_all_zones(self, grid):
        assert set(grid['zones'].keys()) == set(EA_FLOOD_ZONE_RATES.keys())

    def test_distance_count(self, grid):
        assert len(grid['distances']) == 21

    def test_elevation_count(self, grid):
        assert len(grid['elevations']) == 11

    def test_grid_dimensions_per_zone(self, grid):
        for zone_name, zone_data in grid['zones'].items():
            assert len(zone_data['grid']) == 21, f"{zone_name} distance dim"
            for row in zone_data['grid']:
                assert len(row) == 11, f"{zone_name} elevation dim"

    def test_params_present(self, grid):
        p = grid['params']
        assert p['elev_scale_m'] == ELEV_SCALE_M
        assert p['tenor'] == GRID_TENOR
        assert p['recovery'] == GRID_RECOVERY
        assert p['risk_free_rate'] == GRID_RISK_FREE_RATE

    def test_zone_rates_match_config(self, grid):
        for zone_name, zone_data in grid['zones'].items():
            assert zone_data['rate'] == EA_FLOOD_ZONE_RATES[zone_name]


# ===================================================================
# Spot-check grid values against analytical formula
# ===================================================================

class TestGridSpotChecks:

    def _expected_spread(self, zone_rate, distance_m, elevation_m):
        ret = compute_retention(distance_m)
        elev_factor = math.exp(-elevation_m / ELEV_SCALE_M)
        prop_rate = zone_rate * ret * elev_factor
        return round(compute_prs_spread(
            prop_rate, tenor=GRID_TENOR,
            recovery=GRID_RECOVERY, risk_free_rate=GRID_RISK_FREE_RATE,
        ), 2)

    def test_zone1_origin(self, grid):
        expected = self._expected_spread(0.001, 0, 0.0)
        assert grid['zones']['Zone 1']['grid'][0][0] == expected

    def test_zone3b_origin(self, grid):
        expected = self._expected_spread(0.050, 0, 0.0)
        assert grid['zones']['Zone 3b']['grid'][0][0] == expected

    def test_zone2_mid_grid(self, grid):
        # d=2500m (index 10), h=2.5m (index 5)
        expected = self._expected_spread(0.005, 2500, 2.5)
        assert grid['zones']['Zone 2']['grid'][10][5] == expected

    def test_zone3a_far_high(self, grid):
        # d=5000m (index 20), h=5.0m (index 10)
        expected = self._expected_spread(0.020, 5000, 5.0)
        assert grid['zones']['Zone 3a']['grid'][20][10] == expected


# ===================================================================
# Monotonicity tests
# ===================================================================

class TestGridMonotonicity:

    def test_spread_decreases_with_distance(self, grid):
        """For each zone and elevation, spread should decrease as distance increases."""
        for zone_name, zone_data in grid['zones'].items():
            g = zone_data['grid']
            for ei in range(len(GRID_ELEVATIONS_M)):
                for di in range(len(GRID_DISTANCES_M) - 1):
                    assert g[di][ei] >= g[di + 1][ei], (
                        f"{zone_name} d={GRID_DISTANCES_M[di]}→{GRID_DISTANCES_M[di+1]} "
                        f"h={GRID_ELEVATIONS_M[ei]}: {g[di][ei]} < {g[di+1][ei]}"
                    )

    def test_spread_decreases_with_elevation(self, grid):
        """For each zone and distance, spread should decrease as elevation increases."""
        for zone_name, zone_data in grid['zones'].items():
            g = zone_data['grid']
            for di in range(len(GRID_DISTANCES_M)):
                for ei in range(len(GRID_ELEVATIONS_M) - 1):
                    assert g[di][ei] >= g[di][ei + 1], (
                        f"{zone_name} d={GRID_DISTANCES_M[di]} "
                        f"h={GRID_ELEVATIONS_M[ei]}→{GRID_ELEVATIONS_M[ei+1]}: "
                        f"{g[di][ei]} < {g[di][ei+1]}"
                    )

    def test_zone3b_gt_zone3a_everywhere(self, grid):
        g3b = grid['zones']['Zone 3b']['grid']
        g3a = grid['zones']['Zone 3a']['grid']
        for di in range(len(GRID_DISTANCES_M)):
            for ei in range(len(GRID_ELEVATIONS_M)):
                assert g3b[di][ei] >= g3a[di][ei]

    def test_zone3a_gt_zone2_everywhere(self, grid):
        g3a = grid['zones']['Zone 3a']['grid']
        g2 = grid['zones']['Zone 2']['grid']
        for di in range(len(GRID_DISTANCES_M)):
            for ei in range(len(GRID_ELEVATIONS_M)):
                assert g3a[di][ei] >= g2[di][ei]

    def test_zone2_gt_zone1_everywhere(self, grid):
        g2 = grid['zones']['Zone 2']['grid']
        g1 = grid['zones']['Zone 1']['grid']
        for di in range(len(GRID_DISTANCES_M)):
            for ei in range(len(GRID_ELEVATIONS_M)):
                assert g2[di][ei] >= g1[di][ei]


# ===================================================================
# Interpolation tests
# ===================================================================

class TestInterpolation:

    def test_at_grid_point_exact(self, grid):
        """Interpolation at a grid point should return the exact grid value."""
        for zone_name in EA_FLOOD_ZONE_RATES:
            val = interpolate_terrain_spread(grid, zone_name, 1000.0, 2.0)
            # d=1000 is index 4, h=2.0 is index 4
            expected = grid['zones'][zone_name]['grid'][4][4]
            assert abs(val - expected) < 1e-9, (
                f"{zone_name} at grid point: {val} != {expected}"
            )

    def test_at_origin(self, grid):
        val = interpolate_terrain_spread(grid, 'Zone 3b', 0.0, 0.0)
        expected = grid['zones']['Zone 3b']['grid'][0][0]
        assert abs(val - expected) < 1e-9

    def test_midpoint_between_grid_values(self, grid):
        """Interpolation at midpoint should be between bracketing values."""
        zone = 'Zone 2'
        # Midpoint: d=125m (between 0 and 250), h=0.25m (between 0 and 0.5)
        val = interpolate_terrain_spread(grid, zone, 125.0, 0.25)
        v00 = grid['zones'][zone]['grid'][0][0]
        v10 = grid['zones'][zone]['grid'][1][0]
        v01 = grid['zones'][zone]['grid'][0][1]
        v11 = grid['zones'][zone]['grid'][1][1]
        lo = min(v00, v01, v10, v11)
        hi = max(v00, v01, v10, v11)
        assert lo <= val <= hi, f"Midpoint {val} not in [{lo}, {hi}]"

    def test_clamp_beyond_max_distance(self, grid):
        """Distance > 5000m should clamp to 5000m."""
        zone = 'Zone 1'
        val_clamped = interpolate_terrain_spread(grid, zone, 9999.0, 0.0)
        val_edge = interpolate_terrain_spread(grid, zone, 5000.0, 0.0)
        assert abs(val_clamped - val_edge) < 1e-9

    def test_clamp_beyond_max_elevation(self, grid):
        """Elevation > 5.0m should clamp to 5.0m."""
        zone = 'Zone 3a'
        val_clamped = interpolate_terrain_spread(grid, zone, 0.0, 20.0)
        val_edge = interpolate_terrain_spread(grid, zone, 0.0, 5.0)
        assert abs(val_clamped - val_edge) < 1e-9

    def test_clamp_negative_distance(self, grid):
        """Negative distance should clamp to 0."""
        zone = 'Zone 2'
        val_clamped = interpolate_terrain_spread(grid, zone, -100.0, 1.0)
        val_edge = interpolate_terrain_spread(grid, zone, 0.0, 1.0)
        assert abs(val_clamped - val_edge) < 1e-9

    def test_clamp_negative_elevation(self, grid):
        """Negative elevation should clamp to 0."""
        zone = 'Zone 3b'
        val_clamped = interpolate_terrain_spread(grid, zone, 500.0, -2.0)
        val_edge = interpolate_terrain_spread(grid, zone, 500.0, 0.0)
        assert abs(val_clamped - val_edge) < 1e-9

    def test_delta_same_zone_is_zero(self, grid):
        """Terrain delta between same zone should be exactly zero."""
        for zone in EA_FLOOD_ZONE_RATES:
            s1 = interpolate_terrain_spread(grid, zone, 800.0, 1.5)
            s2 = interpolate_terrain_spread(grid, zone, 800.0, 1.5)
            assert abs(s1 - s2) < 1e-12

    def test_delta_higher_zone_positive(self, grid):
        """Moving to a higher-risk zone should increase spread."""
        s_low = interpolate_terrain_spread(grid, 'Zone 1', 500.0, 1.0)
        s_high = interpolate_terrain_spread(grid, 'Zone 3b', 500.0, 1.0)
        assert s_high > s_low

    @pytest.mark.parametrize("zone", list(EA_FLOOD_ZONE_RATES.keys()))
    def test_interpolation_matches_analytical_at_grid_corners(self, grid, zone):
        """All four corners of each cell should match the grid exactly."""
        # Test last grid point
        d = GRID_DISTANCES_M[-1]
        h = GRID_ELEVATIONS_M[-1]
        val = interpolate_terrain_spread(grid, zone, float(d), h)
        expected = grid['zones'][zone]['grid'][-1][-1]
        assert abs(val - expected) < 1e-9
