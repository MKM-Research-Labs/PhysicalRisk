# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.particle_filter — hand-rolled SMC engine. (part 1 of 4)

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
# systematic_resample
# ===========================================================================


class TestSystematicResample:

    def test_uniform_weights_round_robin(self):
        # With N uniform weights, indices should cover 0..N-1 once each
        # (because cumulative grid hits each cell exactly once).
        n = 8
        weights = np.full(n, 1.0 / n)
        idx = systematic_resample(weights, _rng(1))
        assert sorted(idx) == list(range(n))

    def test_concentrated_weights_pick_dominant(self):
        # All weight on index 2 — every resampled index must be 2.
        weights = np.zeros(5)
        weights[2] = 1.0
        idx = systematic_resample(weights, _rng(2))
        assert (idx == 2).all()

    def test_indices_in_valid_range(self):
        rng = _rng(3)
        for trial in range(20):
            w = rng.uniform(size=10)
            idx = systematic_resample(w, _rng(trial))
            assert idx.min() >= 0
            assert idx.max() <= 9
            assert len(idx) == 10

    def test_frequency_proportional_to_weight(self):
        # Sample many resamplings of a non-uniform weight vector and check
        # that average index frequencies track the weights.
        n = 10
        weights = np.array([0.5, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.05, 0.025, 0.025])
        rng = _rng(7)
        counts = np.zeros(n)
        n_trials = 5000
        for _ in range(n_trials):
            idx = systematic_resample(weights, rng)
            for k in idx:
                counts[k] += 1
        empirical = counts / (n_trials * n)
        # 3% absolute tolerance (systematic resampling has low variance).
        for w, e in zip(weights, empirical):
            assert abs(e - w) < 0.03, f"weight={w}, empirical={e}"

    def test_zero_total_weight_raises(self):
        with pytest.raises(ValueError):
            systematic_resample(np.zeros(5), _rng(11))

    def test_renormalises_unnormalised_input(self):
        # Pass non-normalised weights; result must still be valid indices.
        weights = np.array([2.0, 3.0, 5.0])
        idx = systematic_resample(weights, _rng(13))
        assert len(idx) == 3
        assert idx.min() >= 0 and idx.max() <= 2

    def test_empty_input_returns_empty(self):
        idx = systematic_resample(np.array([]), _rng(17))
        assert len(idx) == 0


# ===========================================================================
# ParticleFilter — lifecycle
# ===========================================================================


class TestInitialize:

    def test_negative_n_raises(self, minimal_config):
        with pytest.raises(ValueError):
            ParticleFilter(n_particles=0, config=minimal_config, rng=_rng(19))

    def test_creates_n_particles(self, minimal_config):
        pf = ParticleFilter(n_particles=50, config=minimal_config, rng=_rng(23))
        pf.initialize()
        assert len(pf.particles) == 50

    def test_uniform_weights(self, minimal_config):
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(29))
        pf.initialize()
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.05) < 1e-12 for w in weights)
        assert sum(weights) == pytest.approx(1.0, abs=1e-12)

    def test_all_particles_at_genesis_time(self, minimal_config):
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(31))
        pf.initialize()
        for p in pf.particles:
            assert p.state.time_hours == 0.0

    def test_records_scenario_per_particle(self, minimal_config):
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(37))
        pf.initialize()
        assert len(pf.scenarios) == 20
        for s in pf.scenarios:
            assert isinstance(s, ScenarioFamily)

    def test_history_starts_with_genesis_state(self, minimal_config):
        pf = ParticleFilter(n_particles=15, config=minimal_config, rng=_rng(41))
        pf.initialize()
        for i, h in enumerate(pf.histories):
            assert len(h) == 1
            assert h[0] == pf.particles[i].state

    def test_genesis_time_default(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(43))
        assert pf.genesis_time == datetime(2026, 1, 1)

    def test_step_count_starts_zero(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(47))
        pf.initialize()
        assert pf.step_count == 0
