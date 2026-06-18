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

"""Tests for models.windspeed.timeseries — multi-hour convenience."""

from datetime import datetime

import pytest

from config.typhoon import RegimeClass, ScenarioFamily
from models.typhoon.data_structures import TyphoonState, TyphoonTrajectory
from models.windspeed import windspeed, windspeed_series


def _trajectory():
    # Three-state straight-east trajectory at constant V_max so the time
    # series tests are about geometry, not intensity change.
    base = dict(
        translation_speed_kmh=30.0, heading_deg=90.0,
        v_max_ms=40.0, r_max_km=30.0, r_outer_km=150.0,
        regime=RegimeClass.STRAIGHT_WESTWARD, land_flag=False,
    )
    states = [
        TyphoonState(longitude=2.0, latitude=5.0, time_hours=0.0, **base),
        TyphoonState(longitude=5.0, latitude=5.0, time_hours=2.0, **base),
        TyphoonState(longitude=8.0, latitude=5.0, time_hours=4.0, **base),
    ]
    return TyphoonTrajectory(
        event_id="EVT-TEST",
        particle_id=0,
        scenario_family=ScenarioFamily.BASELINE,
        genesis_time=datetime(2026, 1, 1),
        states=states,
    )


class TestWindspeedSeries:

    def test_returns_one_value_per_hour(self, minimal_config):
        hours = [0.0, 1.0, 2.0, 3.0, 4.0]
        series = windspeed_series(
            event=_trajectory(), hours=hours, lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        assert len(series) == len(hours)

    def test_peaks_when_storm_centre_passes_nearby(self, minimal_config):
        # The storm centre passes lon=5 at t=2. Query point sits 0.6 deg
        # north (~67 km) — outside R_max=30 so the eye never crosses it.
        # In the outer-decay regime the time series is unimodal: V rises
        # as the storm approaches, peaks at closest approach (~t=2), then
        # falls.
        hours = [0.0, 1.0, 2.0, 3.0, 4.0]
        series = windspeed_series(
            event=_trajectory(), hours=hours, lon=5.0, lat=5.6,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        peak_idx = series.index(max(series))
        assert hours[peak_idx] == 2.0

    def test_matches_pointwise_windspeed(self, minimal_config):
        traj = _trajectory()
        hours = [0.0, 1.0, 2.0]
        series = windspeed_series(
            event=traj, hours=hours, lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        for h, v in zip(hours, series):
            v_single = windspeed(
                event=traj, hour=h, lon=5.0, lat=5.0,
                wind_field_params=minimal_config.wind_field,
                land_mask=minimal_config.land_mask,
            )
            assert v == pytest.approx(v_single, rel=1e-12)

    def test_empty_hours_returns_empty(self, minimal_config):
        series = windspeed_series(
            event=_trajectory(), hours=[], lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        assert series == []
