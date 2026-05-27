# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.transitions — one-step state propagator.

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
