# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for the Manning's velocity / flood propagation model."""

import math

import pytest

from models.floodrisk.velocity import (
    MIN_SLOPE,
    build_property_hydrograph,
    compute_attenuation,
    compute_retention,
    compute_manning_velocity,
    compute_slope,
    compute_travel_time,
)


class TestManningVelocity:
    """Tests for compute_manning_velocity."""

    def test_positive_depth_and_slope(self):
        """Manning velocity at d=1.0m, S=0.005, n=0.04 should be ~1.77 m/s.
        Analytical: v = (1/0.04) * 1^(2/3) * sqrt(0.005) = 25 * 0.0707 ≈ 1.77."""
        v = compute_manning_velocity(1.0, 0.005)
        # v = (1/0.04) * 1^(2/3) * sqrt(0.005) ≈ 25 * 0.0707 ≈ 1.77 m/s
        assert 1.5 < v < 2.0

    def test_zero_depth_returns_zero(self):
        """Zero depth must produce zero velocity (no flow without water)."""
        assert compute_manning_velocity(0.0, 0.005) == 0.0

    def test_negative_depth_returns_zero(self):
        """Negative depth is physically invalid; must return zero velocity."""
        assert compute_manning_velocity(-1.0, 0.005) == 0.0

    def test_zero_roughness_returns_zero(self):
        """Zero roughness coefficient causes division by zero; must return 0."""
        assert compute_manning_velocity(1.0, 0.005, roughness=0.0) == 0.0

    def test_slope_clamped_to_min(self):
        """Slopes below MIN_SLOPE must be clamped to MIN_SLOPE to avoid
        near-zero velocities from numerical noise in flat terrain."""
        # Very small slope should be clamped to MIN_SLOPE
        v = compute_manning_velocity(1.0, 0.0001)
        v_min = compute_manning_velocity(1.0, MIN_SLOPE)
        assert v == v_min

    def test_negative_slope_uses_abs(self):
        """Negative slope (downhill in opposite direction) must use absolute value."""
        v_pos = compute_manning_velocity(1.0, 0.01)
        v_neg = compute_manning_velocity(1.0, -0.01)
        assert v_pos == v_neg

    def test_deeper_water_faster(self):
        """Monotonicity: deeper water must produce higher velocity at constant slope.
        Follows from Manning's v ∝ d^(2/3)."""
        v1 = compute_manning_velocity(0.5, 0.005)
        v2 = compute_manning_velocity(2.0, 0.005)
        assert v2 > v1

    def test_steeper_slope_faster(self):
        """Monotonicity: steeper slope must produce higher velocity at constant depth.
        Follows from Manning's v ∝ S^(1/2)."""
        v1 = compute_manning_velocity(1.0, 0.002)
        v2 = compute_manning_velocity(1.0, 0.01)
        assert v2 > v1


class TestTravelTime:
    """Tests for compute_travel_time."""

    def test_basic_travel_time(self):
        """Travel time for 500m at d=1.0m, S=0.005 should be well under 1 hour.
        At ~1.77 m/s, travel time ≈ 500/1.77/3600 ≈ 0.08 hours."""
        # 500m distance, 1m depth, 0.005 slope
        t = compute_travel_time(500, 1.0, 0.005)
        assert 0 < t < 1.0  # Should be well under an hour

    def test_zero_depth_infinite(self):
        """Zero depth produces zero velocity, so travel time must be infinite."""
        t = compute_travel_time(500, 0.0, 0.005)
        assert t == float('inf')

    def test_farther_takes_longer(self):
        """Monotonicity: greater distance must produce longer travel time."""
        t1 = compute_travel_time(200, 1.0, 0.005)
        t2 = compute_travel_time(1000, 1.0, 0.005)
        assert t2 > t1

    def test_zero_distance(self):
        """Zero distance must produce zero travel time."""
        t = compute_travel_time(0, 1.0, 0.005)
        assert t == 0.0


class TestRetention:
    """Tests for compute_retention (distance-based signal retention)."""

    def test_zero_distance_full_strength(self):
        """At zero distance, retention must be 1.0 (full signal)."""
        assert compute_retention(0) == 1.0

    def test_at_length_scale(self):
        """At distance = characteristic length, factor must equal 1/e ≈ 0.368.
        This is the definition of exponential decay length."""
        f = compute_retention(10000, 10000)
        assert abs(f - 1.0 / math.e) < 0.001

    def test_near_river_high_retention(self):
        """At 800m with default 10km length scale, retention ≈ 0.923."""
        f = compute_retention(800)
        assert 0.90 <= f <= 0.95

    def test_one_km_retention(self):
        """At 1km with default 10km length scale, retention ≈ 0.905."""
        f = compute_retention(1000)
        assert 0.88 <= f <= 0.93

    def test_far_distance_near_zero(self):
        """At 5x the decay length, retention should be < 1%."""
        f = compute_retention(50000, 10000)
        assert f < 0.01

    def test_negative_distance(self):
        """Negative distance is clamped to zero; must return 1.0."""
        assert compute_retention(-100) == 1.0

    def test_zero_length(self):
        """Zero decay length means instant decay; must return 0.0."""
        assert compute_retention(100, 0) == 0.0

    def test_backwards_compat_alias(self):
        """compute_attenuation is a backwards-compatible alias."""
        assert compute_attenuation(800) == compute_retention(800)


class TestComputeSlope:
    """Tests for compute_slope."""

    def test_basic_slope(self):
        """Slope from 10m to 8m over 1000m should be 0.002 (2m/1000m)."""
        s = compute_slope(10.0, 8.0, 1000.0)
        assert abs(s - 0.002) < 1e-6

    def test_min_slope_clamp(self):
        """Flat terrain (equal elevations) must return MIN_SLOPE, not zero."""
        # Very flat terrain
        s = compute_slope(10.0, 10.0, 1000.0)
        assert s == MIN_SLOPE

    def test_zero_distance(self):
        """Zero horizontal distance must return MIN_SLOPE to avoid division by zero."""
        s = compute_slope(10.0, 8.0, 0.0)
        assert s == MIN_SLOPE

    def test_slope_is_absolute(self):
        """Slope must be the same regardless of flow direction (uses absolute value)."""
        s1 = compute_slope(10.0, 8.0, 1000.0)
        s2 = compute_slope(8.0, 10.0, 1000.0)
        assert s1 == s2


class TestBuildPropertyHydrograph:
    """Tests for build_property_hydrograph."""

    @pytest.fixture
    def gauge_readings(self):
        """Simple triangular hydrograph: rises 0-10, peaks at 10, falls 10-20."""
        readings = []
        for h in range(21):
            if h <= 10:
                level = 5.0 + (h / 10.0) * 3.0  # 5.0 -> 8.0
            else:
                level = 8.0 - ((h - 10) / 10.0) * 3.0  # 8.0 -> 5.0
                level = max(level, 5.0)
            readings.append({'hour': h, 'water_level_m': level})
        return readings

    def test_empty_readings(self):
        """Empty gauge readings must return empty property hydrograph."""
        assert build_property_hydrograph([], 8.0, 1.0, 0.9, 6.0, 0.3) == []

    def test_output_length_matches_input(self, gauge_readings):
        """Property hydrograph must have same number of time steps as gauge input."""
        result = build_property_hydrograph(
            gauge_readings, 8.0, 1.0, 0.9, 6.0, 0.3
        )
        assert len(result) == len(gauge_readings)

    def test_all_hours_present(self, gauge_readings):
        """Every hour from 0..n must be present in output, in order."""
        result = build_property_hydrograph(
            gauge_readings, 8.0, 1.0, 0.9, 6.0, 0.3
        )
        hours = [r['hour'] for r in result]
        assert hours == list(range(len(gauge_readings)))

    def test_no_flooding_before_arrival(self, gauge_readings):
        """With travel time of 5 hours, first 5 hours must show zero flood depth."""
        result = build_property_hydrograph(
            gauge_readings, 8.0, 5.0, 0.9, 6.0, 0.3
        )
        # First 5 hours should not be flooded
        for r in result[:5]:
            assert r['depth_m'] == 0.0
            assert r['flooded'] is False

    def test_high_floor_prevents_flooding(self, gauge_readings):
        """When floor level exceeds peak WSE, no time step should be flooded."""
        # Floor level so high water never overtops
        result = build_property_hydrograph(
            gauge_readings, 7.0, 0.0, 0.5, 6.5, 2.0
        )
        for r in result:
            assert r['flooded'] is False

    def test_peak_produces_flooding(self, gauge_readings):
        """Low-elevation property at gauge location must flood at peak water level."""
        # Low elevation, no step, close to gauge
        result = build_property_hydrograph(
            gauge_readings, 8.0, 0.0, 1.0, 5.0, 0.0
        )
        # At peak, WSE should be ~8.0, depth ~3.0
        peak_depths = [r['depth_m'] for r in result]
        assert max(peak_depths) > 0

    def test_each_entry_has_required_keys(self, gauge_readings):
        """Each hydrograph entry must contain hour, wse_m, depth_m, and flooded."""
        result = build_property_hydrograph(
            gauge_readings, 8.0, 1.0, 0.9, 6.0, 0.3
        )
        for r in result:
            assert 'hour' in r
            assert 'wse_m' in r
            assert 'depth_m' in r
            assert 'flooded' in r

    def test_depth_never_negative(self, gauge_readings):
        """Flood depth must be non-negative at every time step."""
        result = build_property_hydrograph(
            gauge_readings, 8.0, 1.0, 0.9, 6.0, 0.3
        )
        for r in result:
            assert r['depth_m'] >= 0.0
