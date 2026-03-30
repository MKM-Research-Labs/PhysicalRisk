# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Sensitivity analysis for the flood propagation model (v2.3).

Sweeps distance, elevation, and travel time to verify that retention
is applied consistently and produces physically sensible transmission
rates. Each test class isolates one parameter while holding others
constant, checking monotonicity and boundary behavior.

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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _triangular_gauge_readings(n_hours=168, peak_hour=84, base=2.0, peak=8.0):
    """Build a symmetric triangular gauge hydrograph."""
    readings = []
    for h in range(n_hours):
        if h <= peak_hour:
            level = base + (peak - base) * (h / peak_hour)
        else:
            level = peak - (peak - base) * ((h - peak_hour) / (n_hours - peak_hour))
            level = max(level, base)
        readings.append({'hour': h, 'water_level_m': level})
    return readings


def _compute_flood_depth(gauge_readings, peak_level_m, severe_level,
                         gauge_elevation, prop_elevation, floor_level,
                         distance_m):
    """
    Reproduce the v2.3 _build_flood_event logic for a single storm.

    Returns (flood_depth, retention, est_depth, n_flooded_hours).
    """
    water_above_gauge = max(0.0, peak_level_m - severe_level)
    retention = compute_retention(distance_m)
    water_at_property = water_above_gauge * retention

    height_diff = max(0.0, prop_elevation - gauge_elevation)
    flood_threshold = height_diff + floor_level
    est_depth = max(0.0, water_at_property - flood_threshold)

    # Hydrograph peak WSE — v2.3 uses attenuated value
    absolute_peak_wse = gauge_elevation + water_at_property

    slope = compute_slope(gauge_elevation, prop_elevation, distance_m)
    if est_depth > 0:
        travel_time = compute_travel_time(distance_m, est_depth, slope)
        if travel_time == float('inf'):
            travel_time = 0.0
    else:
        travel_time = 0.0

    readings = build_property_hydrograph(
        gauge_readings, absolute_peak_wse, travel_time,
        retention, prop_elevation, floor_level,
    )

    flood_depth = max((r['depth_m'] for r in readings), default=0.0)
    n_flooded = sum(1 for r in readings if r['flooded'])

    return flood_depth, retention, est_depth, n_flooded


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
        """Property 10km from gauge with moderate storm should not flood."""
        # Use a weaker storm: only 1m above severe (marginal)
        moderate_peak = self.SEVERE + 1.0
        moderate_readings = _triangular_gauge_readings(
            peak=moderate_peak, base=self.SEVERE)
        depth, ret, _, _ = _compute_flood_depth(
            moderate_readings, moderate_peak, self.SEVERE,
            self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, 10000
        )
        assert depth == 0.0, (
            f"10km property with 1m water should not flood, got depth={depth}")
        assert ret < 0.05, f"Retention at 10km should be <5%, got {ret}"

    def test_retention_values_at_key_distances(self, gauge_readings):
        """Verify retention factor at key distances with 3km length scale."""
        cases = [
            (0, 1.0),
            (500, math.exp(-500 / 3000)),
            (1000, math.exp(-1000 / 3000)),
            (3000, math.exp(-1)),     # ≈ 0.368
            (6000, math.exp(-2)),     # ≈ 0.135
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


# ---------------------------------------------------------------------------
# Travel time sensitivity
# ---------------------------------------------------------------------------

class TestTravelTimeSensitivity:
    """Verify travel time behavior: delayed arrival, peak shift, duration."""

    GAUGE_ELEV = 5.0
    PROP_ELEV = 6.5
    FLOOR = 0.3
    SEVERE = 4.0
    PEAK_LEVEL = 10.0

    @pytest.fixture
    def gauge_readings(self):
        return _triangular_gauge_readings(
            n_hours=168, peak_hour=84,
            peak=self.PEAK_LEVEL, base=self.SEVERE
        )

    def test_travel_time_increases_with_distance(self):
        """Travel time must increase monotonically with distance."""
        depth = 1.0
        slope = 0.002
        distances = [100, 500, 1000, 2000, 5000]
        times = [compute_travel_time(d, depth, slope) for d in distances]
        for i in range(1, len(times)):
            assert times[i] > times[i - 1]

    def test_travel_time_decreases_with_depth(self):
        """Deeper water flows faster → shorter travel time."""
        distance = 1000
        slope = 0.002
        depths = [0.1, 0.5, 1.0, 2.0, 5.0]
        times = [compute_travel_time(distance, d, slope) for d in depths]
        for i in range(1, len(times)):
            assert times[i] < times[i - 1]

    def test_arrival_delayed_by_distance(self, gauge_readings):
        """Flood arrival hour should increase with distance."""
        arrivals = []
        for dist in [100, 500, 1000, 3000]:
            _, _, _, n_flooded = _compute_flood_depth(
                gauge_readings, self.PEAK_LEVEL, self.SEVERE,
                self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, dist
            )

            # Build hydrograph to get arrival time
            retention = compute_retention(dist)
            water_above = max(0.0, self.PEAK_LEVEL - self.SEVERE)
            water_at_prop = water_above * retention
            absolute_peak = self.GAUGE_ELEV + water_at_prop
            height_diff = max(0.0, self.PROP_ELEV - self.GAUGE_ELEV)
            est_depth = max(0.0, water_at_prop - (height_diff + self.FLOOR))
            slope = compute_slope(self.GAUGE_ELEV, self.PROP_ELEV, dist)

            if est_depth > 0:
                tt = compute_travel_time(dist, est_depth, slope)
                if tt == float('inf'):
                    tt = 0.0
            else:
                tt = 0.0

            readings = build_property_hydrograph(
                gauge_readings, absolute_peak, tt,
                retention, self.PROP_ELEV, self.FLOOR,
            )

            arrival = None
            for r in readings:
                if r['flooded']:
                    arrival = r['hour']
                    break
            if arrival is not None:
                arrivals.append((dist, arrival))

        # At least 2 distances should flood, and arrival should be later
        # for more distant properties
        assert len(arrivals) >= 2, (
            f"Need at least 2 flooding distances, got {len(arrivals)}"
        )
        for i in range(1, len(arrivals)):
            assert arrivals[i][1] >= arrivals[i - 1][1], (
                f"Arrival at {arrivals[i][0]}m (h={arrivals[i][1]}) < "
                f"arrival at {arrivals[i-1][0]}m (h={arrivals[i-1][1]})"
            )

    def test_flood_duration_decreases_with_distance(self, gauge_readings):
        """More distant properties should have shorter flood duration
        (fewer flooded hours) due to retention."""
        durations = []
        for dist in [100, 500, 1000, 2000]:
            _, _, _, n_flooded = _compute_flood_depth(
                gauge_readings, self.PEAK_LEVEL, self.SEVERE,
                self.GAUGE_ELEV, self.PROP_ELEV, self.FLOOR, dist
            )
            durations.append((dist, n_flooded))

        # Filter to distances that actually flood
        flooded_durations = [(d, n) for d, n in durations if n > 0]
        if len(flooded_durations) >= 2:
            for i in range(1, len(flooded_durations)):
                assert flooded_durations[i][1] <= flooded_durations[i - 1][1], (
                    f"Duration at {flooded_durations[i][0]}m "
                    f"({flooded_durations[i][1]}h) > "
                    f"duration at {flooded_durations[i-1][0]}m "
                    f"({flooded_durations[i-1][1]}h)"
                )


# ---------------------------------------------------------------------------
# Estimator / hydrograph consistency (the v2.3 fix)
# ---------------------------------------------------------------------------

class TestEstimatorHydrographConsistency:
    """Verify that the estimator (est_depth) and hydrograph (flood_depth)
    agree on whether a property floods — the core v2.3 fix."""

    GAUGE_ELEV = 5.0
    SEVERE = 4.0

    @pytest.fixture
    def gauge_readings(self):
        return _triangular_gauge_readings(peak=10.0, base=4.0)

    @pytest.mark.parametrize("distance,prop_elev,floor,peak", [
        (100, 6.0, 0.3, 8.0),      # close, low, moderate storm
        (500, 7.0, 0.3, 10.0),     # medium distance, higher, strong storm
        (1000, 6.5, 0.5, 9.0),     # 1km, mid elevation, medium storm
        (2000, 6.0, 0.3, 7.0),     # far, low, weak storm
        (3000, 7.5, 0.0, 10.0),    # far, high, strong storm, no floor
        (500, 5.5, 0.8, 6.0),      # close, near gauge, high floor, weak
        (200, 8.0, 0.3, 10.0),     # close, very high, strong
        (5000, 6.0, 0.0, 12.0),    # very far, low, extreme storm
    ])
    def test_estimator_agrees_with_hydrograph(self, gauge_readings,
                                               distance, prop_elev,
                                               floor, peak):
        """If est_depth says no flood, hydrograph should also show no flood.
        If est_depth > 0, hydrograph should show flooding."""
        readings = _triangular_gauge_readings(peak=peak, base=self.SEVERE)
        depth, _, est, _ = _compute_flood_depth(
            readings, peak, self.SEVERE,
            self.GAUGE_ELEV, prop_elev, floor, distance
        )

        if est == 0.0:
            assert depth == 0.0, (
                f"Estimator says no flood (est_depth=0) but hydrograph "
                f"shows depth={depth:.4f} at d={distance}m, "
                f"elev={prop_elev}m, floor={floor}m, peak={peak}m"
            )
        else:
            assert depth > 0, (
                f"Estimator says flood (est_depth={est:.4f}) but hydrograph "
                f"shows depth=0 at d={distance}m, "
                f"elev={prop_elev}m, floor={floor}m, peak={peak}m"
            )
