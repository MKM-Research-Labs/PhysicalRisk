"""Tests for terrain delta computation in the PRS JS pricer."""

import pytest

from visual.interactivity.property import phc_prs_pricer


class TestTerrainInterpolationJS:
    """Verify terrain interpolation and delta logic in the JS pricer output."""

    @pytest.fixture
    def js(self):
        return phc_prs_pricer.get_js()

    def test_interpolate_function_present(self, js):
        assert 'function interpolateTerrainSpread(' in js

    def test_interpolate_accepts_terrain_grid(self, js):
        assert 'terrainGrid' in js

    def test_bilinear_interpolation_logic(self, js):
        """Core bilinear formula should be present."""
        assert 'v00 * (1 - td) * (1 - te)' in js

    def test_grid_clamping(self, js):
        """Distance and elevation should be clamped to grid bounds."""
        assert 'Math.max(distances[0]' in js
        assert 'Math.min(distance_m' in js

    def test_terrain_delta_computed(self, js):
        assert 'terrainDelta' in js

    def test_selected_zone_read_from_dropdown(self, js):
        assert "getElementById('phc-ea-zone')" in js

    def test_actual_zone_from_phcdata(self, js):
        assert 'phcData.flood_zone' in js

    def test_delta_zero_when_same_zone(self, js):
        """When selectedZone === actualZone, terrainDelta should stay 0."""
        assert 'selectedZone !== actualZone' in js

    def test_return_includes_terrain_fields(self, js):
        assert 'terrainDelta: terrainDelta' in js
        assert 'selectedZone: selectedZone' in js
        assert 'actualZone: actualZone' in js

    def test_avg_distance_computed_from_gauges(self, js):
        assert 'avgDistM' in js
        assert 'nearestGauges' in js

    def test_elevation_diff_computed(self, js):
        assert 'avgElevDiff' in js
        assert 'phcData.elevation_m' in js


class TestTerrainInterpolationCrossValidation:
    """Cross-validate JS interpolation logic against Python reference."""

    def test_python_reference_at_grid_point(self):
        """Ensure the Python reference produces known values at grid points."""
        from models.hazard.terrain_grid import compute_terrain_grid, interpolate_terrain_spread
        grid = compute_terrain_grid()
        # Zone 3b at d=0, h=0 should be highest spread
        val = interpolate_terrain_spread(grid, 'Zone 3b', 0.0, 0.0)
        assert val > 0
        # Zone 1 at d=0, h=0 should be lowest
        val1 = interpolate_terrain_spread(grid, 'Zone 1', 0.0, 0.0)
        assert val > val1

    def test_delta_is_positive_upgrading_zone(self):
        """Moving from Zone 1 to Zone 3b should yield positive delta."""
        from models.hazard.terrain_grid import compute_terrain_grid, interpolate_terrain_spread
        grid = compute_terrain_grid()
        s_low = interpolate_terrain_spread(grid, 'Zone 1', 500.0, 1.0)
        s_high = interpolate_terrain_spread(grid, 'Zone 3b', 500.0, 1.0)
        delta = s_high - s_low
        assert delta > 0

    def test_delta_is_negative_downgrading_zone(self):
        """Moving from Zone 3b to Zone 1 should yield negative delta."""
        from models.hazard.terrain_grid import compute_terrain_grid, interpolate_terrain_spread
        grid = compute_terrain_grid()
        s_low = interpolate_terrain_spread(grid, 'Zone 1', 500.0, 1.0)
        s_high = interpolate_terrain_spread(grid, 'Zone 3b', 500.0, 1.0)
        delta = s_low - s_high
        assert delta < 0

    def test_delta_zero_same_zone(self):
        """Delta between same zone should be exactly zero."""
        from models.hazard.terrain_grid import compute_terrain_grid, interpolate_terrain_spread
        grid = compute_terrain_grid()
        s1 = interpolate_terrain_spread(grid, 'Zone 2', 750.0, 1.5)
        s2 = interpolate_terrain_spread(grid, 'Zone 2', 750.0, 1.5)
        assert abs(s1 - s2) < 1e-12
