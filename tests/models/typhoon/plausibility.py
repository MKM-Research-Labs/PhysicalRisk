# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.plausibility — soft-constraint scoring.

Covers each component:
  - heading_jump_score: smooth, monotonic in |Δψ|, weight/sigma disabling
  - speed_jump_score: smooth, monotonic in |Δu|, weight/sigma disabling
  - basin_boundary_score: 1.0 inside, smooth decay outside, weight disabling
  - regime_consistency_score: standardised deviation behaviour, STALLED
    example from the spec, weight disabling

And the composer:
  - plausibility_score is the product of components, bounded in (0, 1]
  - "perfect" trajectory (no jumps, inside basin, on regime) -> 1.0
  - one weight up demonstrably tightens that dimension at fixed seed
  - hand-crafted "bad" trajectory accumulates a low cumulative score

Plus the ParticleFilter adapter:
  - make_particle_plausibility wraps the composer for compute_weights
  - prev_state=None returns 1.0 cleanly
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from config.typhoon import (
    PlausibilityWeights,
)
from models.typhoon.data_structures import (
    RegimeClass,
    ScenarioFamily,
    TyphoonParticle,
    TyphoonState,
)
from models.typhoon.plausibility import (
    basin_boundary_score,
    heading_jump_score,
    make_particle_plausibility,
    plausibility_score,
    regime_consistency_score,
    speed_jump_score,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _state(
    lon=5.0,
    lat=5.0,
    speed=18.0,
    heading=270.0,
    regime=RegimeClass.STRAIGHT_WESTWARD,
    v=40.0,
    r_max=35.0,
    r_outer=150.0,
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


# ===========================================================================
# heading_jump_score
# ===========================================================================


class TestHeadingJumpScore:

    def test_no_jump_is_one(self):
        s = _state(heading=270.0)
        prev = _state(heading=270.0)
        assert heading_jump_score(s, prev, weight=0.1, sigma_deg=30.0) == 1.0

    def test_monotonic_in_delta(self):
        # Score must strictly decrease as the jump grows.
        prev = _state(heading=270.0)
        scores = [
            heading_jump_score(_state(heading=h), prev, 0.1, 30.0)
            for h in (270.0, 280.0, 300.0, 330.0, 0.0)
        ]
        for a, b in zip(scores, scores[1:]):
            assert b < a

    def test_circular_delta_uses_short_arc(self):
        # 350 -> 10 is a 20 deg jump, not 340.
        prev = _state(heading=350.0)
        s = _state(heading=10.0)
        score = heading_jump_score(s, prev, weight=0.1, sigma_deg=30.0)
        # Equivalent to a +20 deg jump on the same scale.
        equivalent = heading_jump_score(
            _state(heading=20.0), _state(heading=0.0), 0.1, 30.0,
        )
        assert score == pytest.approx(equivalent, abs=1e-12)

    def test_in_zero_to_one_range(self):
        prev = _state(heading=270.0)
        for h in np.linspace(0.0, 359.0, 36):
            score = heading_jump_score(_state(heading=h), prev, 0.5, 30.0)
            assert 0.0 < score <= 1.0

    def test_zero_weight_disables(self):
        prev = _state(heading=0.0)
        s = _state(heading=180.0)
        assert heading_jump_score(s, prev, weight=0.0, sigma_deg=30.0) == 1.0

    def test_non_positive_sigma_disables(self):
        prev = _state(heading=0.0)
        s = _state(heading=90.0)
        assert heading_jump_score(s, prev, weight=1.0, sigma_deg=0.0) == 1.0
        assert heading_jump_score(s, prev, weight=1.0, sigma_deg=-5.0) == 1.0


# ===========================================================================
# speed_jump_score
# ===========================================================================


class TestSpeedJumpScore:

    def test_no_jump_is_one(self):
        s = _state(speed=20.0)
        prev = _state(speed=20.0)
        assert speed_jump_score(s, prev, weight=0.1, sigma_kmh=10.0) == 1.0

    def test_monotonic_in_delta(self):
        prev = _state(speed=20.0)
        scores = [
            speed_jump_score(_state(speed=s_kmh), prev, 0.1, 10.0)
            for s_kmh in (20.0, 22.0, 30.0, 50.0, 100.0)
        ]
        for a, b in zip(scores, scores[1:]):
            assert b < a

    def test_in_zero_to_one_range(self):
        prev = _state(speed=20.0)
        for s_kmh in (0.0, 5.0, 20.0, 50.0, 200.0):
            score = speed_jump_score(_state(speed=s_kmh), prev, 0.5, 10.0)
            assert 0.0 < score <= 1.0

    def test_zero_weight_disables(self):
        s = _state(speed=100.0)
        prev = _state(speed=0.0)
        assert speed_jump_score(s, prev, weight=0.0, sigma_kmh=10.0) == 1.0

    def test_non_positive_sigma_disables(self):
        s = _state(speed=100.0)
        prev = _state(speed=0.0)
        assert speed_jump_score(s, prev, weight=1.0, sigma_kmh=0.0) == 1.0


# ===========================================================================
# basin_boundary_score
# ===========================================================================


class TestBasinBoundaryScore:

    @pytest.fixture
    def bbox(self):
        return (115.0, 15.0, 125.0, 20.0)

    def test_inside_is_one(self, bbox):
        s = _state(lon=120.0, lat=18.0)
        assert basin_boundary_score(s, bbox, weight=0.5) == 1.0

    def test_on_boundary_is_one(self, bbox):
        s = _state(lon=125.0, lat=20.0)
        assert basin_boundary_score(s, bbox, weight=0.5) == 1.0

    def test_outside_degrades_smoothly(self, bbox):
        # 1 degree outside the eastern boundary
        s_close = _state(lon=126.0, lat=18.0)
        s_far = _state(lon=130.0, lat=18.0)
        score_close = basin_boundary_score(s_close, bbox, weight=0.1)
        score_far = basin_boundary_score(s_far, bbox, weight=0.1)
        assert 0.0 < score_far < score_close < 1.0

    def test_diagonal_outside_counts_both_axes(self, bbox):
        # Outside on both lon and lat: penalty is larger than either alone.
        s_lon_only = _state(lon=130.0, lat=18.0)   # 5 deg lon overshoot
        s_lat_only = _state(lon=120.0, lat=25.0)   # 5 deg lat overshoot
        s_diag = _state(lon=130.0, lat=25.0)       # both
        score_diag = basin_boundary_score(s_diag, bbox, weight=0.1)
        score_lon = basin_boundary_score(s_lon_only, bbox, weight=0.1)
        score_lat = basin_boundary_score(s_lat_only, bbox, weight=0.1)
        # Diagonal overshoot has larger total distance, lower score.
        assert score_diag < score_lon
        assert score_diag < score_lat

    def test_zero_weight_disables(self, bbox):
        s = _state(lon=500.0, lat=80.0)   # absurdly outside
        assert basin_boundary_score(s, bbox, weight=0.0) == 1.0


# ===========================================================================
# regime_consistency_score
# ===========================================================================


class TestRegimeConsistencyScore:

    def test_on_regime_means_score_is_one(self, minimal_config):
        # State sits exactly at the regime's climatological mean -> z = 0
        # for both axes -> score = 1.
        motion = minimal_config.motion
        regime = RegimeClass.STRAIGHT_WESTWARD
        s = _state(
            speed=motion.mean_speed_kmh[regime],
            heading=motion.mean_heading_deg[regime],
            regime=regime,
        )
        assert regime_consistency_score(s, motion, weight=1.0) == 1.0

    def test_stalled_with_fast_speed_is_penalised(self, minimal_config):
        # Spec example: STALLED should have low u. Build a config in which
        # STALLED has very low mean and sigma, then a fast state on STALLED
        # gets a large standardised deviation -> low score.
        motion = replace(
            minimal_config.motion,
            mean_speed_kmh={**minimal_config.motion.mean_speed_kmh, RegimeClass.STALLED: 3.0},
            sigma_speed_kmh={**minimal_config.motion.sigma_speed_kmh, RegimeClass.STALLED: 2.0},
        )
        on_regime = _state(
            speed=3.0,
            heading=motion.mean_heading_deg[RegimeClass.STALLED],
            regime=RegimeClass.STALLED,
        )
        fast = _state(
            speed=30.0,    # ~13 sigma away
            heading=motion.mean_heading_deg[RegimeClass.STALLED],
            regime=RegimeClass.STALLED,
        )
        on_score = regime_consistency_score(on_regime, motion, weight=0.1)
        fast_score = regime_consistency_score(fast, motion, weight=0.1)
        assert fast_score < on_score
        assert fast_score < 0.001    # very heavily penalised

    def test_zero_weight_disables(self, minimal_config):
        # Even an extreme off-regime state scores 1.0 when weight is zero.
        s = _state(speed=999.0, heading=99.0, regime=RegimeClass.STRAIGHT_WESTWARD)
        assert regime_consistency_score(s, minimal_config.motion, weight=0.0) == 1.0

    def test_missing_regime_yields_one(self):
        # If the motion params don't have the state's regime, score = 1.0.
        from config.typhoon import MotionParams
        empty = MotionParams()
        s = _state(regime=RegimeClass.STRAIGHT_WESTWARD)
        assert regime_consistency_score(s, empty, weight=1.0) == 1.0


# ===========================================================================
# plausibility_score (composer)
# ===========================================================================


class TestPlausibilityComposer:

    def test_score_in_zero_to_one_range(self, minimal_config):
        # Perfect transition: same heading and speed, inside basin, on regime.
        regime = RegimeClass.STRAIGHT_WESTWARD
        motion = minimal_config.motion
        prev = _state(
            lon=5.0, lat=5.0,
            speed=motion.mean_speed_kmh[regime],
            heading=motion.mean_heading_deg[regime],
            regime=regime,
        )
        s = _state(
            lon=4.5, lat=5.0,
            speed=motion.mean_speed_kmh[regime],
            heading=motion.mean_heading_deg[regime],
            regime=regime,
        )
        score = plausibility_score(s, prev, minimal_config)
        assert score == pytest.approx(1.0, abs=1e-9)

    def test_score_is_product_of_components(self, minimal_config):
        # Build a state that hits all four penalties at once and check the
        # composite equals the analytical product.
        regime = RegimeClass.STRAIGHT_WESTWARD
        weights = minimal_config.plausibility
        bbox = minimal_config.genesis_prior.bbox
        motion = minimal_config.motion

        prev = _state(lon=5.0, lat=5.0, speed=20.0, heading=270.0, regime=regime)
        # Push the state outside the test bbox (0, 0, 10, 10) by ~5 deg
        # in lon and ~2 deg in lat — engages the basin-boundary penalty
        # together with the heading / speed / regime penalties.
        s = _state(lon=15.0, lat=12.0, speed=60.0, heading=120.0, regime=regime)

        expected = (
            heading_jump_score(s, prev, weights.heading_jump_weight, weights.heading_jump_sigma_deg)
            * speed_jump_score(s, prev, weights.speed_jump_weight, weights.speed_jump_sigma_kmh)
            * basin_boundary_score(s, bbox, weights.basin_boundary_weight)
            * regime_consistency_score(s, motion, weights.regime_consistency_weight)
        )
        assert plausibility_score(s, prev, minimal_config) == pytest.approx(expected, abs=1e-12)

    def test_tightening_one_weight_lowers_score(self, minimal_config):
        prev = _state(heading=270.0)
        s = _state(heading=240.0)   # 30 deg jump
        loose = plausibility_score(s, prev, minimal_config)
        tight_cfg = replace(
            minimal_config,
            plausibility=replace(minimal_config.plausibility, heading_jump_weight=2.0),
        )
        tight = plausibility_score(s, prev, tight_cfg)
        assert tight < loose

    def test_moderate_bad_case_is_small_but_positive(self, minimal_config):
        # A clearly bad-but-not-pathological transition stays detectably
        # positive (the engine relies on this so resampling has a non-zero
        # mass to redistribute when ESS is low). The state below stays
        # inside the test bbox so only the heading and speed-jump penalties
        # bite — keeps the score above the float underflow regime.
        prev = _state(lon=5.0, lat=5.0, speed=15.0, heading=270.0)
        s = _state(lon=5.0, lat=5.0, speed=40.0, heading=200.0)
        score = plausibility_score(s, prev, minimal_config)
        assert 0.0 < score < 1.0

    def test_extreme_inputs_underflow_to_non_negative(self, minimal_config):
        # An absurdly bad transition can underflow to 0.0 in IEEE 754. The
        # particle filter's compute_weights handles zero-total weights by
        # resetting to uniform, so the contract on this function is only
        # "non-negative", not "strictly positive".
        prev = _state(lon=5.0, lat=5.0, speed=10.0, heading=270.0)
        s = _state(lon=85.0, lat=80.0, speed=300.0, heading=90.0)
        assert plausibility_score(s, prev, minimal_config) >= 0.0

    def test_bad_trajectory_accumulates_low_score(self, minimal_config):
        # Spec acceptance: a hand-crafted "bad" trajectory should accumulate
        # a low cumulative score over 24 steps. Construct each step to
        # violate every component significantly.
        regime = RegimeClass.STALLED
        # Tighten the weights enough to make the penalty bite.
        cfg = replace(
            minimal_config,
            plausibility=PlausibilityWeights(
                heading_jump_weight=1.0,
                speed_jump_weight=1.0,
                basin_boundary_weight=1.0,
                regime_consistency_weight=1.0,
                heading_jump_sigma_deg=30.0,
                speed_jump_sigma_kmh=10.0,
            ),
            motion=replace(
                minimal_config.motion,
                mean_speed_kmh={**minimal_config.motion.mean_speed_kmh, RegimeClass.STALLED: 3.0},
                sigma_speed_kmh={**minimal_config.motion.sigma_speed_kmh, RegimeClass.STALLED: 2.0},
            ),
        )
        product = 1.0
        for i in range(24):
            # alternating large heading flip + speed flip, outside the bbox
            prev = _state(
                lon=130.0 + i * 0.1, lat=25.0,
                speed=5.0 if i % 2 == 0 else 80.0,
                heading=0.0 if i % 2 == 0 else 180.0,
                regime=regime,
            )
            s = _state(
                lon=130.0 + i * 0.1, lat=25.0,
                speed=80.0 if i % 2 == 0 else 5.0,
                heading=180.0 if i % 2 == 0 else 0.0,
                regime=regime,
            )
            product *= plausibility_score(s, prev, cfg)
        # Sanity: 24 steps with each step strongly penalised must collapse.
        assert product < 1e-6


# ===========================================================================
# make_particle_plausibility (adapter)
# ===========================================================================


class TestParticleAdapter:

    def test_returns_callable(self, minimal_config):
        fn = make_particle_plausibility(minimal_config)
        assert callable(fn)

    def test_none_prev_state_yields_one(self, minimal_config):
        fn = make_particle_plausibility(minimal_config)
        p = TyphoonParticle(state=_state(), weight=1.0, particle_id=0)
        assert fn(p, None) == 1.0

    def test_delegates_to_composer(self, minimal_config):
        fn = make_particle_plausibility(minimal_config)
        prev = _state(heading=270.0)
        s = _state(heading=240.0)
        p = TyphoonParticle(state=s, weight=1.0, particle_id=0)
        assert fn(p, prev) == pytest.approx(plausibility_score(s, prev, minimal_config), abs=1e-12)

    def test_wires_into_particle_filter(self, minimal_config):
        """End-to-end smoke: pass the adapter through run_to_horizon."""
        from models.typhoon.particle_filter import ParticleFilter
        rng = np.random.default_rng(0)
        fn = make_particle_plausibility(minimal_config)
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=rng)
        trajectories = pf.run_to_horizon(
            horizon_hours=24.0, dt_hours=1.0, plausibility_fn=fn,
        )
        assert len(trajectories) == 20
        # Weights remain non-negative throughout (already enforced inside
        # compute_weights, but worth asserting at the integration boundary).
        for p in pf.particles:
            assert p.weight >= 0.0

    def test_scenario_family_unaffected_by_plausibility(self, minimal_config):
        # Plausibility may reassign particles via resampling, but each new
        # particle still carries a valid ScenarioFamily.
        from models.typhoon.particle_filter import ParticleFilter
        rng = np.random.default_rng(1)
        fn = make_particle_plausibility(minimal_config)
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=rng)
        pf.run_to_horizon(
            horizon_hours=12.0, dt_hours=1.0, plausibility_fn=fn,
            ess_threshold_frac=0.99,    # force resampling
        )
        assert all(isinstance(s, ScenarioFamily) for s in pf.scenarios)
