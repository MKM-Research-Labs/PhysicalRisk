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

"""Tests for models.typhoon.particle_filter — hand-rolled SMC engine. (part 4 of 4)

Covers:
- systematic_resample: returns N valid indices, frequency proportional to
  weight, rejects zero-total weights
- initialize: N particles, uniform weights, all at genesis time, each has
  a scenario family from the prior mix
- propagate_one_step: advances all particles, preserves IDs and weights
- compute_weights: renormalises to sum 1, handles zero-total gracefully
- effective_sample_size: N under uniform weights, 1 for a delta
- resample: weights reset to 1/N, parent IDs preserved, ESS recovers to N
- run_to_horizon: returns N trajectories with the correct number of states,
  no plausibility -> no collapse (all genesis particle_ids preserved)
- Reproducibility under fixed seed
- Acceptance criterion: 1000 particles x 168 hours produces a diverse
  ensemble (spread in peak winds) without trajectory collapse
"""

from datetime import datetime

import numpy as np
import pytest

from config.typhoon import ScenarioFamily
from models.typhoon.data_structures import TyphoonParticle, TyphoonTrajectory
from models.typhoon.particle_filter import (
    ParticleFilter,
    systematic_resample,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _rng(seed=4096):
    return np.random.default_rng(seed)


# ===========================================================================
# ParticleFilter — run_to_horizon
# ===========================================================================


class TestRunToHorizon:

    def test_returns_n_trajectories(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(149))
        trajectories = pf.run_to_horizon(horizon_hours=5.0, dt_hours=1.0)
        assert len(trajectories) == 10
        for t in trajectories:
            assert isinstance(t, TyphoonTrajectory)

    def test_each_trajectory_has_genesis_plus_steps(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(151))
        trajectories = pf.run_to_horizon(horizon_hours=10.0, dt_hours=1.0)
        for t in trajectories:
            assert len(t.states) == 11   # genesis (t=0) + 10 hourly steps

    def test_auto_initialises(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(157))
        # No explicit initialize() — run_to_horizon must handle it.
        trajectories = pf.run_to_horizon(horizon_hours=3.0)
        assert len(trajectories) == 5

    def test_horizon_defaults_to_config(self, minimal_config):
        pf = ParticleFilter(n_particles=3, config=minimal_config, rng=_rng(163))
        trajectories = pf.run_to_horizon(dt_hours=24.0)
        # config.horizon_hours = 168, dt = 24 -> 7 steps -> 8 states each.
        assert all(len(t.states) == 8 for t in trajectories)

    def test_no_plausibility_means_no_collapse(self, minimal_config):
        # Without a plausibility_fn the filter never resamples, so every
        # genesis particle_id is still present at horizon.
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(167))
        trajectories = pf.run_to_horizon(horizon_hours=20.0, dt_hours=1.0)
        # The particle_id on the trajectory is the current particle id.
        # Without resampling, no parent_id should be set (still None on all
        # particles).
        for p in pf.particles:
            assert p.parent_id is None

    def test_trajectory_carries_scenario_family(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(173))
        trajectories = pf.run_to_horizon(horizon_hours=3.0)
        for t in trajectories:
            assert isinstance(t.scenario_family, ScenarioFamily)

    def test_plausibility_triggers_resample_when_concentrated(self, minimal_config):
        # A plausibility function that scores particles by their id alone
        # produces concentrated weights — eventually the ESS dips below the
        # threshold and resample fires, populating parent_id.
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(179))
        trajectories = pf.run_to_horizon(
            horizon_hours=10.0,
            dt_hours=1.0,
            plausibility_fn=lambda p, prev: float(p.particle_id + 1),
            ess_threshold_frac=0.99,    # force resampling almost every step
        )
        # After resampling at least once, every new particle has a parent_id.
        # The first resample establishes the population; subsequent ones may
        # collapse further. Confirm parent_id was populated.
        assert any(p.parent_id is not None for p in pf.particles)
        assert len(trajectories) == 20


# ===========================================================================
# Reproducibility
# ===========================================================================


class TestReproducibility:

    def test_same_seed_same_trajectories(self, minimal_config):
        pf_a = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(181))
        pf_b = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(181))
        a = pf_a.run_to_horizon(horizon_hours=5.0, dt_hours=1.0)
        b = pf_b.run_to_horizon(horizon_hours=5.0, dt_hours=1.0)
        for ta, tb in zip(a, b):
            assert ta.states == tb.states


# ===========================================================================
# Phase 1.4 acceptance criterion
# ===========================================================================


class TestEnsembleDiversity:
    """Phase 1.4 acceptance: 1000 particles x 168 hours produces a diverse
    ensemble, not a collapsed one. Concrete check: the peak-wind
    distribution at horizon spans a meaningful range."""

    def test_thousand_particles_produce_diverse_peak_winds(self, minimal_config):
        pf = ParticleFilter(n_particles=1000, config=minimal_config, rng=_rng(191))
        trajectories = pf.run_to_horizon(horizon_hours=168.0, dt_hours=1.0)
        peak_winds = np.array([
            max(s.v_max_ms for s in t.states) for t in trajectories
        ])
        # The IQR of the peak-wind distribution should be at least 5 m/s --
        # any narrower would indicate trajectory collapse / loss of breadth.
        q25, q75 = float(np.quantile(peak_winds, 0.25)), float(np.quantile(peak_winds, 0.75))
        assert q75 - q25 > 5.0
        # Standard deviation > 3 m/s under any reasonable Phase 1 config.
        assert float(np.std(peak_winds)) > 3.0
