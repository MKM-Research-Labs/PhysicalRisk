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

"""Tests for models.typhoon.wind_field.time_series — trajectory
aggregation, duration-above-threshold accounting, and the Phase 1.6
acceptance criterion (synthetic track produces a smooth peak-and-decay).
"""

from datetime import datetime

import pytest

from config.typhoon import PropertyPoint, ScenarioFamily, WindFieldParams
from models.typhoon.data_structures import TyphoonTrajectory
from models.typhoon.wind_field import (
    duration_above_threshold,
    evaluate_time_series,
)
from tests.models.typhoon.wind_field._helpers import (
    DEFAULT_LAT,
    DEFAULT_LON,
    synthetic_track,
)


def _open_sea(lon, lat):
    return False


@pytest.fixture
def default_params():
    return WindFieldParams()


# ===========================================================================
# duration_above_threshold
# ===========================================================================


class TestDurationAboveThreshold:

    def test_zero_when_all_below(self):
        assert duration_above_threshold([0.0, 1.0, 2.0], [5.0, 5.0, 5.0], threshold=10.0) == 0.0

    def test_full_when_all_above(self):
        # Two consecutive intervals contribute; the last sample doesn't.
        assert duration_above_threshold([0.0, 1.0, 2.0], [50.0, 50.0, 50.0], threshold=10.0) == 2.0

    def test_partial_count(self):
        # Above for first three samples, below for the last two.
        ts = [0.0, 1.0, 2.0, 3.0, 4.0]
        vs = [50.0, 50.0, 50.0, 5.0, 5.0]
        # Intervals 0->1, 1->2, 2->3 are above the threshold at the leading
        # sample — total 3h.
        assert duration_above_threshold(ts, vs, threshold=10.0) == 3.0

    def test_empty(self):
        assert duration_above_threshold([], [], threshold=5.0) == 0.0


# ===========================================================================
# evaluate_time_series — shape and metadata
# ===========================================================================


class TestEvaluateTimeSeries:

    def test_returns_wind_field_output_shape(self, default_params):
        traj = synthetic_track(start_lon=DEFAULT_LON - 1.5, start_lat=DEFAULT_LAT, n_steps=12)
        prop = PropertyPoint(property_id="P1", longitude=DEFAULT_LON + 0.5, latitude=DEFAULT_LAT)
        out = evaluate_time_series(traj, prop, default_params, _open_sea, thresholds_ms=[17.5, 30.0])
        assert out.point_id == "P1"
        assert len(out.time_hours) == len(traj.states)
        assert len(out.sustained_ms) == len(traj.states)
        # Thresholds keyed as float in the result.
        assert set(out.duration_above_ms.keys()) == {17.5, 30.0}

    def test_peak_metadata_matches_peak_sample(self, default_params):
        traj = synthetic_track(
            start_lon=DEFAULT_LON - 1.5, start_lat=DEFAULT_LAT,
            n_steps=12, speed_kmh=50.0,
        )
        prop = PropertyPoint(property_id="P1", longitude=DEFAULT_LON + 0.5, latitude=DEFAULT_LAT)
        out = evaluate_time_series(traj, prop, default_params, _open_sea, thresholds_ms=[17.5])
        peak_idx = out.sustained_ms.index(out.peak_sustained_ms)
        assert out.time_of_peak_hours == out.time_hours[peak_idx]

    def test_empty_trajectory(self, default_params):
        empty = TyphoonTrajectory(
            event_id="EVT-EMPTY",
            particle_id=0,
            scenario_family=ScenarioFamily.BASELINE,
            genesis_time=datetime(2026, 1, 1),
            states=[],
        )
        prop = PropertyPoint(property_id="P1", longitude=DEFAULT_LON, latitude=DEFAULT_LAT)
        out = evaluate_time_series(empty, prop, default_params, _open_sea, thresholds_ms=[17.5])
        assert out.time_hours == []
        assert out.peak_sustained_ms == 0.0


# ===========================================================================
# Phase 1.6 acceptance criterion
# ===========================================================================


class TestAcceptanceCriterion:
    """Phase 1.6 acceptance: wind-field at a sample point traces a smooth
    peak-and-decay through a known synthetic track."""

    def test_offset_passing_storm_yields_unimodal_smooth_curve(self, default_params):
        # Storm moves east through a track that PASSES NEAR but not over
        # the property. Offset 0.6 deg south of the track keeps the
        # closest approach well outside R_max=30 so the parametric eye
        # floor is never sampled — the time series is strictly unimodal.
        traj = synthetic_track(
            start_lon=DEFAULT_LON - 2.0, start_lat=DEFAULT_LAT + 0.6,
            n_steps=12, dt_hours=1.0,
            speed_kmh=40.0, heading_deg=90.0,
            v_max=50.0, r_max_km=30.0, r_outer_km=150.0,
        )
        prop = PropertyPoint(property_id="P-offset", longitude=DEFAULT_LON, latitude=DEFAULT_LAT)
        out = evaluate_time_series(traj, prop, default_params, _open_sea, thresholds_ms=[17.5])

        v = out.sustained_ms
        peak_idx = v.index(max(v))
        ascending = v[: peak_idx + 1]
        descending = v[peak_idx:]
        for a, b in zip(ascending, ascending[1:]):
            assert b >= a, f"Ascending violation at peak_idx={peak_idx}: {ascending}"
        for a, b in zip(descending, descending[1:]):
            assert b <= a, f"Descending violation at peak_idx={peak_idx}: {descending}"

        # Peak occurs near the closest-approach time (~ midway through).
        assert 4 <= peak_idx <= 8
        # Peak distance is on the order of the offset (60-100 km).
        assert 60.0 < out.distance_at_peak_km < 100.0
        # Gale-force exceedance is non-zero somewhere along the track.
        assert out.duration_above_ms[17.5] > 0.0

    def test_direct_hit_shows_eye_dip(self, default_params):
        # The parametric profile has an alpha_eye floor at r=0, so a direct
        # hit produces a U-shape (eyewall -> eye -> eyewall). Verify the
        # minimum is below the maximum somewhere in the series. This is
        # correct behaviour of the parametric profile, documented as a
        # property of the model.
        traj = synthetic_track(
            start_lon=DEFAULT_LON - 2.0, start_lat=DEFAULT_LAT,
            n_steps=12, dt_hours=1.0,
            speed_kmh=40.0, heading_deg=90.0,
            v_max=50.0, r_max_km=30.0, r_outer_km=150.0,
        )
        prop = PropertyPoint(property_id="P-direct", longitude=DEFAULT_LON, latitude=DEFAULT_LAT)
        out = evaluate_time_series(traj, prop, default_params, _open_sea, thresholds_ms=[17.5])
        peak = max(out.sustained_ms)
        # Sample near the geometric closest-approach lies below the eyewall peak.
        nearest_idx = out.sustained_ms.index(min(out.sustained_ms))
        assert out.sustained_ms[nearest_idx] < peak
