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

"""Tests for models.typhoon.particle_filter — hand-rolled SMC engine. (part 3 of 4)

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
# ParticleFilter — weights
# ===========================================================================


class TestComputeWeights:

    def test_uniform_score_preserves_uniform_weights(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(83))
        pf.initialize()
        pf.compute_weights(lambda p, prev: 1.0)
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.1) < 1e-12 for w in weights)

    def test_renormalises_to_sum_one(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(89))
        pf.initialize()
        pf.compute_weights(lambda p, prev: p.particle_id + 1.0)
        total = sum(p.weight for p in pf.particles)
        assert total == pytest.approx(1.0, abs=1e-12)

    def test_zero_total_falls_back_to_uniform(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(97))
        pf.initialize()
        # Every particle scored zero — engine must not divide by zero, must
        # not stop the simulation; weights reset to uniform.
        pf.compute_weights(lambda p, prev: 0.0)
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.1) < 1e-12 for w in weights)

    def test_rejects_negative_scores(self, minimal_config):
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(101))
        pf.initialize()
        with pytest.raises(ValueError):
            pf.compute_weights(lambda p, prev: -1.0)

    def test_prev_state_is_previous_history_entry(self, minimal_config):
        # After one propagate step, prev_state should be the genesis state
        # for every particle.
        pf = ParticleFilter(n_particles=5, config=minimal_config, rng=_rng(102))
        pf.initialize()
        genesis_states = [list(h) for h in pf.histories]   # snapshot before propagate
        pf.propagate_one_step()
        captured = []
        pf.compute_weights(lambda p, prev: (captured.append(prev), 1.0)[1])
        for i, prev in enumerate(captured):
            assert prev == genesis_states[i][0]

    def test_prev_state_is_none_before_any_propagation(self, minimal_config):
        # Called right after initialize, history has only the genesis state,
        # so there is no prev_state.
        pf = ParticleFilter(n_particles=3, config=minimal_config, rng=_rng(103))
        pf.initialize()
        captured = []
        pf.compute_weights(lambda p, prev: (captured.append(prev), 1.0)[1])
        for prev in captured:
            assert prev is None


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
        pf.compute_weights(lambda p, prev: p.particle_id + 1.0)
        pf.resample()
        weights = [p.weight for p in pf.particles]
        assert all(abs(w - 0.1) < 1e-12 for w in weights)

    def test_particle_count_preserved(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(113))
        pf.initialize()
        pf.compute_weights(lambda p, prev: p.particle_id + 1.0)
        pf.resample()
        assert len(pf.particles) == 10
        assert len(pf.histories) == 10
        assert len(pf.scenarios) == 10

    def test_new_ids_are_zero_to_n(self, minimal_config):
        pf = ParticleFilter(n_particles=10, config=minimal_config, rng=_rng(127))
        pf.initialize()
        pf.compute_weights(lambda p, prev: p.particle_id + 1.0)
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
        pf.compute_weights(lambda p, prev: 1.0 if p.particle_id == 0 else 0.01)
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
