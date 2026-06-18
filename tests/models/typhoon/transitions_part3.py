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

"""Tests for models.typhoon.transitions — one-step state propagator (part 3 of 4).

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
# update_size
# ===========================================================================


class TestUpdateSize:

    def test_returns_positive_radii(self, minimal_config):
        rng = _rng(31)
        for _ in range(200):
            v = float(rng.uniform(15.0, 80.0))
            s = _state(v=v, r_max=30.0, r_outer=120.0)
            r_max, r_outer = update_size(s, v, minimal_config.size, rng)
            assert r_max > 0.0
            assert r_outer > 0.0

    def test_invariant_r_max_lt_r_outer_always(self, minimal_config):
        rng = _rng(37)
        for _ in range(2000):
            v = float(rng.uniform(15.0, 80.0))
            s = _state(v=v, r_max=30.0, r_outer=120.0)
            r_max, r_outer = update_size(s, v, minimal_config.size, rng)
            assert r_max < r_outer

    def test_mean_reversion_moves_toward_target(self):
        # With zero noise and a large pull, R_max should jump close to its
        # V-conditional target in one step.
        params = SizeParams(
            r_max_intercept_log_km=4.0,    # exp(4) ~ 54.6 km
            r_max_v_coef=0.0,
            r_max_sigma_log=0.0,
            r_outer_intercept_log_km=5.0,
            r_outer_v_coef=0.0,
            r_outer_sigma_log=0.0,
            mean_reversion_rate=1.0,
        )
        rng = _rng(41)
        s = _state(r_max=10.0, r_outer=20.0, v=40.0)
        r_max, _ = update_size(s, 40.0, params, rng)
        # With pull=1.0, R_max should jump entirely to target.
        assert r_max == pytest.approx(math.exp(4.0), abs=1e-6)


# ===========================================================================
# step()
# ===========================================================================


class TestStep:

    def test_returns_typhoon_state(self, minimal_config):
        rng = _rng(43)
        s = _state()
        s2 = step(s, minimal_config, rng)
        assert isinstance(s2, TyphoonState)

    def test_time_advances(self, minimal_config):
        rng = _rng(47)
        s = _state(t=12.0)
        s2 = step(s, minimal_config, rng, dt_hours=1.0)
        assert s2.time_hours == pytest.approx(13.0, abs=1e-9)

    def test_dt_scaling_applies_to_time(self, minimal_config):
        rng = _rng(53)
        s = _state(t=0.0)
        s2 = step(s, minimal_config, rng, dt_hours=2.5)
        assert s2.time_hours == pytest.approx(2.5, abs=1e-9)

    def test_regime_unchanged(self, minimal_config):
        rng = _rng(59)
        for regime in RegimeClass:
            s = _state(regime=regime)
            s2 = step(s, minimal_config, rng)
            assert s2.regime is regime

    def test_invariants_preserved_over_many_steps(self, minimal_config):
        rng = _rng(61)
        s = _state()
        for _ in range(200):
            s = step(s, minimal_config, rng)
            assert s.r_max_km < s.r_outer_km
            assert s.v_max_ms >= 0.0
            assert -90.0 <= s.latitude <= 90.0
            assert 0.0 <= s.heading_deg < 360.0
            assert s.translation_speed_kmh >= 0.0

    def test_land_flag_evaluated_at_new_position(self, minimal_config):
        # Wrap the config with a land mask that knows where the next step
        # will land and confirm the resulting state has the correct flag.
        rng = _rng(67)
        s = _state(lon=120.0, lat=18.0, speed=20.0, heading=270.0, land=False)
        cfg = _config_with_overrides(
            minimal_config,
            land_mask=lambda lon, lat: lon < 119.5,
        )
        s2 = step(s, cfg, rng, dt_hours=1.0)
        # With ~111 km/h westward, dt=1h, we move ~1 deg west: new lon ~ 119.0.
        # The land mask returns True for lon < 119.5.
        assert s2.land_flag == (s2.longitude < 119.5)

    def test_fixed_seed_reproducible(self, minimal_config):
        rng_a = _rng(71)
        rng_b = _rng(71)
        s = _state()
        a = step(s, minimal_config, rng_a)
        b = step(s, minimal_config, rng_b)
        assert a == b
