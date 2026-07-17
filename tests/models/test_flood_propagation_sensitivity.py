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
Sensitivity analysis for the flood propagation model (v2.3) — distance
and elevation sweeps.

Verifies that retention is applied consistently and produces physically
sensible transmission rates when sweeping distance and property elevation.

Run with: pytest tests/models/test_flood_propagation_sensitivity.py -v
"""

import math

import pytest

from models.floodrisk.velocity import (
    build_property_hydrograph,
    compute_retention,
    compute_travel_time,
    compute_slope,
)

from tests.models._flood_propagation_helpers import (
    _triangular_gauge_readings,
    _compute_flood_depth,
)


# ---------------------------------------------------------------------------
# Distance sensitivity
# ---------------------------------------------------------------------------

class TestDistanceSensitivity:
    """Sweep distance from 0 to 10 km; flood depth must decrease monotonically."""

    DISTANCES = [0, 50, 100, 200, 500, 1000, 2000, 3000, 5000, 8000, 10000]

    # Fixed property: 2m above gauge, 0.3m floor step
    GAUGE_ELEV = 5.0
    PROP_ELEV = 7.0
    FLOOR = 0.3
    SEVERE = 4.0
    PEAK_LEVEL = 10.0  # 6m above severe → strong flood signal

    @pytest.fixture
    def gauge_readings(self):
        return _triangular_gauge_readings(peak=self.PEAK_LEVEL, base=self.SEVERE)

    def test_flood_depth_decreases_with_distance(self, gauge_readings):
        """More distant properties receive less water — flood depth must
        decrease monotonically with distance."""
        depths = []
        for d in self.DISTANCES:
            depth, _, _, _ = _compute_flood_depth(
                gauge_readings, self.PEAK_LEVEL, self.SEVERE,
                self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, max(d, 1)
            )
            depths.append(depth)

        for i in range(1, len(depths)):
            assert depths[i] <= depths[i - 1] + 1e-6, (
                f"Depth at {self.DISTANCES[i]}m ({depths[i]:.4f}) > "
                f"depth at {self.DISTANCES[i-1]}m ({depths[i-1]:.4f})"
            )

    def test_close_property_floods(self, gauge_readings):
        """Property 50m from gauge with strong storm must flood."""
        depth, ret, _, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, 50
        )
        assert depth > 0, "50m property should flood with 6m water above gauge"
        assert ret > 0.98, f"Retention at 50m should be ~0.98, got {ret}"

    def test_distant_property_does_not_flood(self, gauge_readings):
        """Property 50km from gauge with moderate storm should not flood."""
        # Use a weaker storm: only 1m above severe (marginal)
        moderate_peak = self.SEVERE + 1.0
        moderate_readings = _triangular_gauge_readings(
            peak=moderate_peak, base=self.SEVERE)
        depth, ret, _, _ = _compute_flood_depth(
            moderate_readings, moderate_peak, self.SEVERE,
            self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, 50000
        )
        assert depth == 0.0, (
            f"50km property with 1m water should not flood, got depth={depth}")
        assert ret < 0.01, f"Retention at 50km should be <1%, got {ret}"

    def test_retention_values_at_key_distances(self, gauge_readings):
        """Verify retention factor at key distances with 10km length scale."""
        cases = [
            (0, 1.0),
            (500, math.exp(-500 / 10000)),
            (1000, math.exp(-1000 / 10000)),
            (10000, math.exp(-1)),     # ≈ 0.368
            (20000, math.exp(-2)),     # ≈ 0.135
        ]
        for dist, expected in cases:
            actual = compute_retention(dist)
            assert abs(actual - expected) < 0.001, (
                f"Retention at {dist}m: expected {expected:.4f}, got {actual:.4f}")

    def test_transmission_rate_realistic(self, gauge_readings):
        """At typical Thames distances (200-800m), check flood/no-flood
        split across a range of storm severities."""
        n_storms = 20
        n_flooded = 0
        for i in range(n_storms):
            # Storm peaks from severe+0.5 to severe+10.5
            peak = self.SEVERE + 0.5 + i * 0.5
            readings = _triangular_gauge_readings(peak=peak, base=self.SEVERE)
            depth, _, _, _ = _compute_flood_depth(
                readings, peak, self.SEVERE,
                self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, 636
            )
            if depth > 0:
                n_flooded += 1

        ratio = n_flooded / n_storms * 100
        assert 10 <= ratio <= 90, (
            f"Transmission at 636m: {ratio:.0f}% — expected between 10-90%"
        )
        assert n_flooded < n_storms, (
            "Not all storms should flood a property 636m away"
        )


# ---------------------------------------------------------------------------
# Elevation sensitivity
# ---------------------------------------------------------------------------

class TestElevationSensitivity:
    """Sweep property elevation; flood depth must decrease as elevation rises."""

    ELEVATIONS_ABOVE_GAUGE = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]

    GAUGE_ELEV = 5.0
    FLOOR = 0.3
    SEVERE = 4.0
    PEAK_LEVEL = 10.0
    DISTANCE = 500  # 500m, retention ≈ 0.847

    @pytest.fixture
    def gauge_readings(self):
        return _triangular_gauge_readings(peak=self.PEAK_LEVEL, base=self.SEVERE)

    def test_flood_depth_decreases_with_elevation(self, gauge_readings):
        """Higher properties must have lower (or equal) flood depth."""
        depths = []
        for delta in self.ELEVATIONS_ABOVE_GAUGE:
            prop_elev = self.GAUGE_ELEV + delta
            depth, _, _, _ = _compute_flood_depth(
                gauge_readings, self.PEAK_LEVEL, self.SEVERE,
                self.GAUGE_ELEV, prop_elev, self.FLOOR, self.DISTANCE
            )
            depths.append(depth)

        for i in range(1, len(depths)):
            assert depths[i] <= depths[i - 1] + 1e-6, (
                f"Depth at +{self.ELEVATIONS_ABOVE_GAUGE[i]}m "
                f"({depths[i]:.4f}) > depth at "
                f"+{self.ELEVATIONS_ABOVE_GAUGE[i-1]}m ({depths[i-1]:.4f})"
            )

    def test_low_elevation_floods(self, gauge_readings):
        """Property only 0.5m above gauge should flood with a strong storm."""
        prop_elev = self.GAUGE_ELEV + 0.5
        depth, _, _, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, prop_elev, self.FLOOR, self.DISTANCE
        )
        assert depth > 0, "Low-elevation property should flood"

    def test_high_elevation_does_not_flood(self, gauge_readings):
        """Property 8m above gauge should not flood (water_at_property < threshold)."""
        prop_elev = self.GAUGE_ELEV + 8.0
        depth, _, est, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, prop_elev, self.FLOOR, self.DISTANCE
        )
        assert depth == 0.0, (
            f"Property 8m above gauge should not flood, got depth={depth}"
        )
        assert est == 0.0, "Estimator should also show no flood"

    def test_floor_level_raises_threshold(self, gauge_readings):
        """Higher floor level should reduce flood depth."""
        prop_elev = self.GAUGE_ELEV + 2.0
        depth_low_floor, _, _, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, prop_elev, 0.0, self.DISTANCE
        )
        depth_high_floor, _, _, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, prop_elev, 1.0, self.DISTANCE
        )
        assert depth_low_floor >= depth_high_floor, (
            f"Floor 0.0m depth ({depth_low_floor:.4f}) < "
            f"floor 1.0m depth ({depth_high_floor:.4f})"
        )

    def test_elevation_threshold_boundary(self, gauge_readings):
        """Find the elevation where flooding stops — should be consistent
        between estimator and hydrograph."""
        retention = compute_retention(self.DISTANCE)
        water_above = max(0.0, self.PEAK_LEVEL - self.SEVERE)
        water_at_prop = water_above * retention
        # Theoretical max elevation difference that still floods:
        # water_at_prop > height_diff + floor
        max_height_diff = water_at_prop - self.FLOOR

        # Property just below threshold should flood
        prop_below = self.GAUGE_ELEV + max_height_diff - 0.1
        depth_below, _, est_below, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, prop_below, self.FLOOR, self.DISTANCE
        )

        # Property just above threshold should not flood
        prop_above = self.GAUGE_ELEV + max_height_diff + 0.1
        depth_above, _, est_above, _ = _compute_flood_depth(
            gauge_readings, self.PEAK_LEVEL, self.SEVERE,
            self.GAUGE_ELEV, prop_above, self.FLOOR, self.DISTANCE
        )

        assert depth_below > 0, (
            f"Property 0.1m below threshold should flood "
            f"(est_depth={est_below:.4f})"
        )
        assert depth_above == 0.0, (
            f"Property 0.1m above threshold should not flood "
            f"(est_depth={est_above:.4f})"
        )
