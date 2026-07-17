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

"""Tests for models.typhoon.transitions — one-step state propagator (part 4 of 4).

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
# advance()
# ===========================================================================


class TestAdvance:

    def test_returns_n_states(self, minimal_config):
        rng = _rng(73)
        trajectory = advance(_state(), minimal_config, rng, n_steps=10)
        assert len(trajectory) == 10

    def test_zero_steps_returns_empty(self, minimal_config):
        rng = _rng(79)
        trajectory = advance(_state(), minimal_config, rng, n_steps=0)
        assert trajectory == []

    def test_negative_raises(self, minimal_config):
        rng = _rng(83)
        with pytest.raises(ValueError):
            advance(_state(), minimal_config, rng, n_steps=-1)

    def test_time_monotonically_increases(self, minimal_config):
        rng = _rng(89)
        trajectory = advance(_state(t=0.0), minimal_config, rng, n_steps=20, dt_hours=1.0)
        times = [s.time_hours for s in trajectory]
        assert times == sorted(times)
        assert times[0] == pytest.approx(1.0, abs=1e-9)
        assert times[-1] == pytest.approx(20.0, abs=1e-9)


# ===========================================================================
# Spec-driven regime behaviour
# ===========================================================================


class TestStraightWestwardLonDecreases:
    """STRAIGHT_WESTWARD: lon should decrease on average over many steps
    when the regime mean heading is westward and noise is moderate."""

    def test_lon_trend_westward(self, minimal_config):
        rng = _rng(91)
        s = _state(
            lon=120.0, lat=15.0,
            speed=20.0, heading=270.0,
            regime=RegimeClass.STRAIGHT_WESTWARD,
        )
        trajectory = advance(s, minimal_config, rng, n_steps=100)
        # On average, longitude should be lower than starting after 100 steps.
        final_lon = trajectory[-1].longitude
        assert final_lon < 120.0


class TestPermanentLandDecaysWindMonotonically:
    """With a land_mask=True everywhere and zero water-side noise, V_max
    must decrease monotonically per the exponential land-decay rule."""

    def test_land_only_decay_is_monotonic(self, minimal_config):
        rng = _rng(97)
        cfg = _config_with_overrides(
            minimal_config,
            land_mask=lambda lon, lat: True,
            intensity=IntensityParams(
                drift_ms_per_hour=0.0,
                sigma_ms_per_hour=0.0,
                k_land_per_hour=0.15,
            ),
        )
        s = _state(v=70.0, land=True)
        trajectory = advance(s, cfg, rng, n_steps=20)
        v_series = [s.v_max_ms for s in trajectory]
        for a, b in zip(v_series, v_series[1:]):
            assert b < a

    def test_land_only_decay_rate_matches_spec(self, minimal_config):
        rng = _rng(101)
        cfg = _config_with_overrides(
            minimal_config,
            land_mask=lambda lon, lat: True,
            intensity=IntensityParams(
                drift_ms_per_hour=0.0,
                sigma_ms_per_hour=0.0,
                k_land_per_hour=0.15,
            ),
        )
        s = _state(v=70.0, land=True)
        trajectory = advance(s, cfg, rng, n_steps=5)
        # After 5 hourly land steps: V * exp(-0.15)^5
        expected = 70.0 * math.exp(-0.15 * 5)
        assert trajectory[-1].v_max_ms == pytest.approx(expected, abs=1e-6)


class TestNwRecurverHeadingDriftsNorth:
    """NW_RECURVER above the recurvature latitude: heading should drift
    toward north over many steps under a config that biases consistently."""

    def test_heading_drifts_north_above_threshold(self, minimal_config):
        # Build a config with strong recurvature bias, low noise, and very
        # high heading persistence so the bias dominates.
        cfg = _config_with_overrides(
            minimal_config,
            motion=replace(
                _zero_noise_motion(minimal_config.motion),
                speed_persistence=1.0,
                heading_persistence=1.0,
                recurvature_latitude=15.0,
                recurvature_bias_deg_per_step=2.0,
                mean_heading_deg={r: 270.0 for r in RegimeClass},
            ),
            # Hold land off so we don't trigger over-land decay.
            land_mask=lambda lon, lat: False,
            intensity=IntensityParams(
                drift_ms_per_hour=0.0, sigma_ms_per_hour=0.0, k_land_per_hour=0.15,
            ),
        )
        rng = _rng(103)
        s = _state(lat=20.0, heading=270.0, regime=RegimeClass.NW_RECURVER, speed=20.0)
        trajectory = advance(s, cfg, rng, n_steps=30)
        # Heading should have rotated clockwise toward 360/0 by at least
        # (n_steps * bias) deg = 60 deg from 270 — capped by reaching 0.
        # After 30 steps: 270 + 30*2 = 330 (still short of north).
        final_heading = trajectory[-1].heading_deg
        assert final_heading > 320.0
        assert final_heading <= 360.0


# ===========================================================================
# RECURVATURE_REGIMES constant — sanity check
# ===========================================================================


class TestRecurvatureRegimesConstant:

    def test_contains_nw_and_sharp_recurve(self):
        assert RegimeClass.NW_RECURVER in RECURVATURE_REGIMES
        assert RegimeClass.SHARP_RECURVE in RECURVATURE_REGIMES

    def test_excludes_other_regimes(self):
        assert RegimeClass.STRAIGHT_WESTWARD not in RECURVATURE_REGIMES
        assert RegimeClass.STALLED not in RECURVATURE_REGIMES
        assert RegimeClass.LANDFALL_DECAY not in RECURVATURE_REGIMES
