# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.particle_filter — hand-rolled SMC engine.

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
    DEFAULT_ESS_THRESHOLD_FRAC,
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


# ===========================================================================
# ParticleFilter — propagate
# ===========================================================================


class TestPropagate:

    def test_must_initialize_first(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(53))
        with pytest.raises(RuntimeError):
            pf.propagate_one_step()

    def test_advances_time_for_all_particles(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(59))
        pf.initialize()
        pf.propagate_one_step(dt_hours=1.0)
        for p in pf.particles:
            assert p.state.time_hours == pytest.approx(1.0, abs=1e-9)

    def test_dt_scaling(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(61))
        pf.initialize()
        pf.propagate_one_step(dt_hours=2.5)
        for p in pf.particles:
            assert p.state.time_hours == pytest.approx(2.5, abs=1e-9)

    def test_preserves_particle_ids(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(67))
        pf.initialize()
        ids_before = [p.particle_id for p in pf.particles]
        pf.propagate_one_step()
        ids_after = [p.particle_id for p in pf.particles]
        assert ids_before == ids_after

    def test_preserves_weights(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(71))
        pf.initialize()
        weights_before = [p.weight for p in pf.particles]
        pf.propagate_one_step()
        weights_after = [p.weight for p in pf.particles]
        assert weights_before == weights_after

    def test_history_grows(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(73))
        pf.initialize()
        pf.propagate_one_step()
        pf.propagate_one_step()
        for h in pf.histories:
            assert len(h) == 3   # genesis + two steps

    def test_step_count_increments(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(79))
        pf.initialize()
        pf.propagate_one_step()
        pf.propagate_one_step()
        pf.propagate_one_step()
        assert pf.step_count == 3


# ===========================================================================
# ParticleFilter — weights
# ===========================================================================


class TestComputeWeights:

    def test_uniform_score_preserves_uniform_weights(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(83))
        pf.initialize()
        pf.compute_weights(lambda p: 1.0)
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.1) < 1e-12 for w in weights)

    def test_renormalises_to_sum_one(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(89))
        pf.initialize()
        pf.compute_weights(lambda p: p.particle_id + 1.0)
        total = sum(p.weight for p in pf.particles)
        assert total == pytest.approx(1.0, abs=1e-12)

    def test_zero_total_falls_back_to_uniform(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(97))
        pf.initialize()
        # Every particle scored zero — engine must not divide by zero, must
        # not stop the simulation; weights reset to uniform.
        pf.compute_weights(lambda p: 0.0)
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.1) < 1e-12 for w in weights)

    def test_rejects_negative_scores(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(101))
        pf.initialize()
        with pytest.raises(ValueError):
            pf.compute_weights(lambda p: -1.0)


# ===========================================================================
# ParticleFilter — ESS
# ===========================================================================


class TestEffectiveSampleSize:

    def test_uniform_weights_gives_n(self, minimal_config):
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(103))
        pf.initialize()
        assert pf.effective_sample_size() == pytest.approx(20.0, abs=1e-9)

    def test_delta_weights_gives_one(self, minimal_config):
        pf = ParticleFilter(n_particles=20, config=minimal_config, rng=_rng(107))
        pf.initialize()
        # Reach in and put all weight on particle 0.
        for i, p in enumerate(pf.particles):
            pf.particles[i] = TyphoonParticle(
                state=p.state,
                weight=1.0 if i == 0 else 0.0,
                particle_id=p.particle_id,
                parent_id=p.parent_id,
            )
        assert pf.effective_sample_size() == pytest.approx(1.0, abs=1e-9)


# ===========================================================================
# ParticleFilter — resample
# ===========================================================================


class TestResample:

    def test_weights_reset_to_uniform(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(109))
        pf.initialize()
        pf.compute_weights(lambda p: p.particle_id + 1.0)
        pf.resample()
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.1) < 1e-12 for w in weights)

    def test_particle_count_preserved(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(113))
        pf.initialize()
        pf.compute_weights(lambda p: p.particle_id + 1.0)
        pf.resample()
        assert len(pf.particles) == 10
        assert len(pf.histories) == 10
        assert len(pf.scenarios) == 10

    def test_new_ids_are_zero_to_n(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(127))
        pf.initialize()
        pf.compute_weights(lambda p: p.particle_id + 1.0)
        pf.resample()
        ids = [p.particle_id for p in pf.particles]
        assert ids == list(range(10))

    def test_parent_ids_populated_from_source(self, minimal_config):
        # Concentrate weight on particles 0 and 1, then resample. Every new
        # parent_id must be either 0 or 1.
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(131))
        pf.initialize()
        # Manually set weights so 0 and 1 share everything.
        for i, p in enumerate(pf.particles):
            pf.particles[i] = TyphoonParticle(
                state=p.state,
                weight=0.5 if i < 2 else 0.0,
                particle_id=p.particle_id,
                parent_id=p.parent_id,
            )
        pf.resample()
        parent_ids = {p.parent_id for p in pf.particles}
        assert parent_ids <= {0, 1}

    def test_ess_recovers_to_n_after_resample(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(137))
        pf.initialize()
        pf.compute_weights(lambda p: 1.0 if p.particle_id == 0 else 0.01)
        ess_before = pf.effective_sample_size()
        assert ess_before < 10.0
        pf.resample()
        assert pf.effective_sample_size() == pytest.approx(10.0, abs=1e-9)

    def test_histories_are_independent_lists(self, minimal_config):
        # After resampling, two new particles that share a parent must have
        # independent history lists so future propagations don't entangle.
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(139))
        pf.initialize()
        pf.propagate_one_step()
        # Concentrate weight on particle 0.
        for i, p in enumerate(pf.particles):
            pf.particles[i] = TyphoonParticle(
                state=p.state,
                weight=1.0 if i == 0 else 0.0,
                particle_id=p.particle_id,
                parent_id=p.parent_id,
            )
        pf.resample()
        # Every new history is a separate list instance.
        ids = {id(h) for h in pf.histories}
        assert len(ids) == 10


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
            plausibility_fn=lambda p: float(p.particle_id + 1),
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
