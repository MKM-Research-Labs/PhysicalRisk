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

"""Tests for models.windspeed.interpolation — linear state interpolation
at arbitrary hours within a trajectory.
"""

import math

import pytest

from config.typhoon import RegimeClass
from models.typhoon.data_structures import TyphoonState
from models.windspeed.interpolation import interpolate_state_at_hour


def _state(lon, lat, v, heading, regime=RegimeClass.STRAIGHT_WESTWARD, land=False, t=0.0,
           speed=15.0, r_max=30.0, r_outer=120.0):
    return TyphoonState(
        longitude=lon, latitude=lat,
        translation_speed_kmh=speed, heading_deg=heading,
        v_max_ms=v, r_max_km=r_max, r_outer_km=r_outer,
        regime=regime, land_flag=land, time_hours=t,
    )


@pytest.fixture
def simple_trajectory():
    # Two states one hour apart, moving east, intensifying from 30 to 50.
    return [
        _state(lon=5.0, lat=5.0, v=30.0, heading=90.0, t=0.0),
        _state(lon=5.5, lat=5.0, v=50.0, heading=90.0, t=1.0),
    ]


class TestInterpolation:

    def test_empty_states_raises(self):
        with pytest.raises(ValueError):
            interpolate_state_at_hour([], hour=0.0)

    def test_before_first_returns_first(self, simple_trajectory):
        s = interpolate_state_at_hour(simple_trajectory, hour=-5.0)
        assert s == simple_trajectory[0]

    def test_after_last_returns_last(self, simple_trajectory):
        s = interpolate_state_at_hour(simple_trajectory, hour=99.0)
        assert s == simple_trajectory[-1]

    def test_at_first_endpoint_returns_first(self, simple_trajectory):
        s = interpolate_state_at_hour(simple_trajectory, hour=0.0)
        assert s == simple_trajectory[0]

    def test_at_second_endpoint_returns_second(self, simple_trajectory):
        s = interpolate_state_at_hour(simple_trajectory, hour=1.0)
        assert s == simple_trajectory[-1]

    def test_midpoint_lerps_continuous_fields(self, simple_trajectory):
        s = interpolate_state_at_hour(simple_trajectory, hour=0.5)
        assert s.longitude == pytest.approx(5.25, abs=1e-9)
        assert s.v_max_ms == pytest.approx(40.0, abs=1e-9)
        assert s.time_hours == pytest.approx(0.5, abs=1e-9)

    def test_heading_circular_short_arc(self):
        # 350° -> 10° should interpolate to 0° at the midpoint, not 180°.
        states = [
            _state(lon=0.0, lat=0.0, v=30.0, heading=350.0, t=0.0),
            _state(lon=0.0, lat=0.0, v=30.0, heading=10.0,  t=1.0),
        ]
        s = interpolate_state_at_hour(states, hour=0.5)
        assert s.heading_deg == pytest.approx(0.0, abs=1e-6)

    def test_regime_takes_nearest_neighbour(self, simple_trajectory):
        # Change the second state's regime; the t<0.5 midpoint keeps the first.
        states = [
            _state(lon=0.0, lat=0.0, v=30.0, heading=90.0, regime=RegimeClass.STRAIGHT_WESTWARD, t=0.0),
            _state(lon=1.0, lat=0.0, v=30.0, heading=90.0, regime=RegimeClass.LANDFALL_DECAY,    t=1.0),
        ]
        early = interpolate_state_at_hour(states, hour=0.3)
        late = interpolate_state_at_hour(states, hour=0.7)
        assert early.regime is RegimeClass.STRAIGHT_WESTWARD
        assert late.regime is RegimeClass.LANDFALL_DECAY

    def test_land_flag_takes_nearest_neighbour(self):
        states = [
            _state(lon=0.0, lat=0.0, v=30.0, heading=90.0, land=False, t=0.0),
            _state(lon=1.0, lat=0.0, v=30.0, heading=90.0, land=True,  t=1.0),
        ]
        early = interpolate_state_at_hour(states, hour=0.4)
        late = interpolate_state_at_hour(states, hour=0.6)
        assert early.land_flag is False
        assert late.land_flag is True

    def test_duplicate_timestamps_return_earlier(self):
        states = [
            _state(lon=0.0, lat=0.0, v=30.0, heading=0.0, t=2.0),
            _state(lon=9.9, lat=9.9, v=99.0, heading=0.0, t=2.0),
        ]
        s = interpolate_state_at_hour(states, hour=2.0)
        # First match wins (the at-first-endpoint check above).
        assert s.longitude == 0.0
