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

"""
Sensitivity analysis for the flood propagation model (v2.3) — travel time
and estimator/hydrograph consistency.

Verifies travel time behavior (delayed arrival, peak shift, duration) and
that the estimator and hydrograph agree on flood/no-flood — the core v2.3 fix.

Run with: pytest tests/models/test_flood_propagation_travel_time.py -v
"""

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
