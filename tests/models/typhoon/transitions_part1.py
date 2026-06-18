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

"""Tests for models.typhoon.transitions — one-step state propagator (part 1 of 4).

Covers:
- Compass-degree helpers (wrap, signed delta)
- Equirectangular position advection (cardinal directions, dt scaling)
- Motion update: speed/heading persistence, regime mean, recurvature bias
- Wind update: over-water drift/noise, over-land exponential decay
- Size update: log-space mean reversion, R_max < R_outer invariant
- step() preserves invariants (regime fixed, time advances, lat in range)
- advance() returns the requested trajectory length
- Spec-driven regime behaviour:
    - STRAIGHT_WESTWARD: lon decreases on average over many steps
    - Over-land state: V decays monotonically under zero noise
    - NW_RECURVER above recurvature_latitude: heading drifts northward
- Reproducibility under fixed seed
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from config.typhoon import (
    CatchmentTyphoonConfig,
    IntensityParams,
    MotionParams,
    PeakWindParams,
    SizeParams,
)
from models.typhoon.data_structures import (
    RegimeClass,
    ScenarioFamily,
    TyphoonState,
)
from models.typhoon.transitions import (
    EARTH_RADIUS_KM,
    RECURVATURE_REGIMES,
    advance,
    haversine_step,
    signed_compass_delta,
    step,
    update_motion,
    update_position,
    update_size,
    update_wind,
    wrap_compass_degrees,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _rng(seed=2024):
    return np.random.default_rng(seed)


def _state(
    lon=120.0,
    lat=18.0,
    speed=20.0,
    heading=270.0,
    v=40.0,
    r_max=35.0,
    r_outer=150.0,
    regime=RegimeClass.STRAIGHT_WESTWARD,
    land=False,
    t=0.0,
):
    return TyphoonState(
        longitude=lon,
        latitude=lat,
        translation_speed_kmh=speed,
        heading_deg=heading,
        v_max_ms=v,
        r_max_km=r_max,
        r_outer_km=r_outer,
        regime=regime,
        land_flag=land,
        time_hours=t,
    )


def _zero_noise_motion(base: MotionParams) -> MotionParams:
    return replace(
        base,
        sigma_speed_kmh={r: 0.0 for r in RegimeClass},
        sigma_heading_deg={r: 0.0 for r in RegimeClass},
    )


def _config_with_overrides(base: CatchmentTyphoonConfig, **overrides) -> CatchmentTyphoonConfig:
    return replace(base, **overrides)


# ===========================================================================
# Compass-degree helpers
# ===========================================================================


class TestWrapCompassDegrees:

    @pytest.mark.parametrize("deg,expected", [
        (0.0, 0.0),
        (45.0, 45.0),
        (360.0, 0.0),
        (720.0, 0.0),
        (-45.0, 315.0),
        (405.0, 45.0),
        (359.999, 359.999),
    ])
    def test_wraps(self, deg, expected):
        assert wrap_compass_degrees(deg) == pytest.approx(expected, abs=1e-6)


class TestSignedCompassDelta:

    @pytest.mark.parametrize("target,current,expected", [
        (0.0, 0.0, 0.0),
        (10.0, 350.0, 20.0),       # short way clockwise
        (350.0, 10.0, -20.0),      # short way counter-clockwise
        (180.0, 0.0, 180.0),       # exact half-turn (sign convention picks +180)
        (90.0, 0.0, 90.0),
        (270.0, 0.0, -90.0),
    ])
    def test_smallest_signed_delta(self, target, current, expected):
        assert signed_compass_delta(target, current) == pytest.approx(expected, abs=1e-9)


# ===========================================================================
# Haversine / equirectangular position advection
# ===========================================================================


class TestHaversineStep:

    def test_east_movement_increases_longitude(self):
        new_lon, new_lat = haversine_step(0.0, 0.0, 100.0, 0.0)
        assert new_lon > 0.0
        assert new_lat == pytest.approx(0.0, abs=1e-9)

    def test_north_movement_increases_latitude(self):
        new_lon, new_lat = haversine_step(0.0, 0.0, 0.0, 100.0)
        assert new_lat > 0.0
        assert new_lon == pytest.approx(0.0, abs=1e-9)

    def test_one_degree_latitude_is_111km(self):
        # 1 deg latitude ~ pi/180 * R = 111.19 km. Move 111.19 km north
        # from equator and check we land near 1.0 N.
        _, new_lat = haversine_step(0.0, 0.0, 0.0, math.pi / 180.0 * EARTH_RADIUS_KM)
        assert new_lat == pytest.approx(1.0, abs=1e-6)

    def test_longitude_wraps_at_dateline(self):
        # Move 1000 km east from lon=179, lat=0 — should wrap into negative
        # longitudes rather than producing 180+.
        new_lon, _ = haversine_step(179.0, 0.0, 1000.0, 0.0)
        assert -180.0 < new_lon <= 180.0
        assert new_lon < 0.0   # we crossed the dateline

    def test_latitude_clamped_to_pole(self):
        # Pushing way north must not exceed +90.
        _, new_lat = haversine_step(0.0, 89.0, 0.0, 10_000.0)
        assert new_lat == 90.0


# ===========================================================================
# update_position
# ===========================================================================


class TestUpdatePosition:

    def test_due_east(self):
        # heading=90 means due east in compass; expect longitude up, lat flat.
        s = _state(lon=0.0, lat=0.0)
        new_lon, new_lat = update_position(s, speed_kmh=111.19, heading_deg=90.0, dt_hours=1.0)
        assert new_lon > 0.0
        assert new_lat == pytest.approx(0.0, abs=1e-6)

    def test_due_north(self):
        s = _state(lon=0.0, lat=0.0)
        new_lon, new_lat = update_position(s, speed_kmh=111.19, heading_deg=0.0, dt_hours=1.0)
        assert new_lat == pytest.approx(1.0, abs=1e-3)
        assert new_lon == pytest.approx(0.0, abs=1e-6)

    def test_due_west(self):
        s = _state(lon=10.0, lat=0.0)
        new_lon, _ = update_position(s, speed_kmh=111.19, heading_deg=270.0, dt_hours=1.0)
        assert new_lon < 10.0

    def test_due_south(self):
        s = _state(lon=0.0, lat=10.0)
        _, new_lat = update_position(s, speed_kmh=111.19, heading_deg=180.0, dt_hours=1.0)
        assert new_lat < 10.0

    def test_dt_scales_distance(self):
        s = _state(lon=0.0, lat=0.0)
        lon_1h, _ = update_position(s, speed_kmh=100.0, heading_deg=90.0, dt_hours=1.0)
        lon_2h, _ = update_position(s, speed_kmh=100.0, heading_deg=90.0, dt_hours=2.0)
        assert lon_2h == pytest.approx(2.0 * lon_1h, rel=1e-6)
