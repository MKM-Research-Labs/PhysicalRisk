# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.transitions — one-step state propagator (part 2 of 4).

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
# update_motion
# ===========================================================================


class TestUpdateMotion:

    def test_returns_valid_speed_and_heading(self, minimal_config):
        rng = _rng(1)
        s = _state()
        for _ in range(100):
            speed, heading = update_motion(s, minimal_config.motion, rng)
            assert speed >= 0.0
            assert 0.0 <= heading < 360.0

    def test_full_persistence_zero_noise_preserves_speed(self, minimal_config):
        # With persistence=1 and zero noise, speed and heading should stay
        # exactly the same as the previous state.
        motion = replace(
            _zero_noise_motion(minimal_config.motion),
            speed_persistence=1.0,
            heading_persistence=1.0,
        )
        rng = _rng(2)
        s = _state(speed=23.0, heading=145.0)
        speed, heading = update_motion(s, motion, rng)
        assert speed == pytest.approx(23.0, abs=1e-9)
        assert heading == pytest.approx(145.0, abs=1e-9)

    def test_zero_persistence_zero_noise_targets_regime_mean(self, minimal_config):
        # With persistence=0 and zero noise, output equals the regime mean.
        motion = replace(
            _zero_noise_motion(minimal_config.motion),
            speed_persistence=0.0,
            heading_persistence=0.0,
        )
        rng = _rng(3)
        s = _state(speed=99.0, heading=10.0)   # far from regime targets
        speed, heading = update_motion(s, motion, rng)
        assert speed == pytest.approx(motion.mean_speed_kmh[s.regime], abs=1e-9)
        assert heading == pytest.approx(motion.mean_heading_deg[s.regime], abs=1e-9)

    def test_recurvature_bias_pulls_heading_toward_north(self, minimal_config):
        # NW_RECURVER above the recurvature latitude with zero noise: heading
        # should move toward 0 (north) by at most the bias step.
        base = minimal_config.motion
        motion = replace(
            _zero_noise_motion(base),
            speed_persistence=1.0,
            heading_persistence=1.0,
            recurvature_latitude=15.0,
            recurvature_bias_deg_per_step=10.0,
            mean_heading_deg={r: 270.0 for r in RegimeClass},  # west — without bias would stay
        )
        rng = _rng(5)
        s = _state(lat=20.0, heading=270.0, regime=RegimeClass.NW_RECURVER)
        _, heading = update_motion(s, motion, rng)
        # 270 with bias toward 0: signed delta 0-270 = +90 (CW). Apply +10.
        assert heading == pytest.approx(280.0, abs=1e-9)

    def test_recurvature_only_applies_above_threshold(self, minimal_config):
        motion = replace(
            _zero_noise_motion(minimal_config.motion),
            speed_persistence=1.0,
            heading_persistence=1.0,
            recurvature_latitude=20.0,
            recurvature_bias_deg_per_step=10.0,
        )
        rng = _rng(7)
        # Below threshold — no bias.
        s = _state(lat=10.0, heading=270.0, regime=RegimeClass.NW_RECURVER)
        _, heading = update_motion(s, motion, rng)
        assert heading == pytest.approx(270.0, abs=1e-9)

    def test_recurvature_does_not_affect_other_regimes(self, minimal_config):
        motion = replace(
            _zero_noise_motion(minimal_config.motion),
            speed_persistence=1.0,
            heading_persistence=1.0,
            recurvature_latitude=15.0,
            recurvature_bias_deg_per_step=10.0,
        )
        rng = _rng(11)
        s = _state(lat=20.0, heading=270.0, regime=RegimeClass.STRAIGHT_WESTWARD)
        _, heading = update_motion(s, motion, rng)
        assert heading == pytest.approx(270.0, abs=1e-9)


# ===========================================================================
# update_wind
# ===========================================================================


class TestUpdateWind:

    def test_land_decay_is_exact_under_zero_noise(self, minimal_config):
        # exp(-k * dt). k=0.15, dt=1 -> factor 0.8607
        rng = _rng(13)
        s = _state(v=50.0)
        v = update_wind(s, minimal_config.intensity, land_flag=True, rng=rng, dt_hours=1.0)
        assert v == pytest.approx(50.0 * math.exp(-0.15), abs=1e-9)

    def test_land_decay_monotonic_multistep(self, minimal_config):
        rng = _rng(17)
        v_prev = 60.0
        for _ in range(20):
            s = _state(v=v_prev)
            v_new = update_wind(s, minimal_config.intensity, land_flag=True, rng=rng, dt_hours=1.0)
            assert v_new < v_prev
            v_prev = v_new

    def test_water_with_zero_drift_and_zero_noise_preserves(self, minimal_config):
        intensity = IntensityParams(drift_ms_per_hour=0.0, sigma_ms_per_hour=0.0)
        rng = _rng(19)
        s = _state(v=42.0)
        v = update_wind(s, intensity, land_flag=False, rng=rng)
        assert v == pytest.approx(42.0, abs=1e-9)

    def test_positive_drift_increases_v_on_average(self, minimal_config):
        intensity = IntensityParams(drift_ms_per_hour=0.5, sigma_ms_per_hour=1.0)
        rng = _rng(23)
        samples = []
        for _ in range(1000):
            s = _state(v=40.0)
            samples.append(update_wind(s, intensity, land_flag=False, rng=rng))
        assert float(np.mean(samples)) > 40.0

    def test_v_never_negative(self, minimal_config):
        # Intensity with large negative drift that would push V below zero
        # mean should still clamp to non-negative.
        intensity = IntensityParams(drift_ms_per_hour=-1000.0, sigma_ms_per_hour=0.0)
        rng = _rng(29)
        s = _state(v=5.0)
        v = update_wind(s, intensity, land_flag=False, rng=rng)
        assert v >= 0.0
