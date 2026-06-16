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
 (part 3 of 3)
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
