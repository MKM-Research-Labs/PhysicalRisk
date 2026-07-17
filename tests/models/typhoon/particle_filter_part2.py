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

"""Tests for models.typhoon.particle_filter — hand-rolled SMC engine. (part 2 of 4)

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
# ParticleFilter — coupled genesis (Stage 3, coupling_spec.md §4)
# ===========================================================================


class TestCoupledInitialize:
    """When genesis_v_max_override is supplied, every particle starts at the
    SAME fixed peak wind and the SAME scenario label — the event's windiness
    is fixed by the paired storm. SMC still explores track/size/location/regime.
    """

    def test_all_particles_share_override_v_max(self, minimal_config):
        pf = ParticleFilter(
            n_particles=30, config=minimal_config, rng=_rng(101),
            genesis_v_max_override=57.5,
            genesis_scenario_override=ScenarioFamily.SEVERE,
        )
        pf.initialize()
        for p in pf.particles:
            assert p.state.v_max_ms == pytest.approx(57.5)

    def test_all_particles_share_scenario_label(self, minimal_config):
        pf = ParticleFilter(
            n_particles=20, config=minimal_config, rng=_rng(103),
            genesis_v_max_override=57.5,
            genesis_scenario_override=ScenarioFamily.EXTREME,
        )
        pf.initialize()
        assert all(s == ScenarioFamily.EXTREME for s in pf.scenarios)

    def test_other_dimensions_still_vary(self, minimal_config):
        # Coupling fixes only Vmax+scenario; location/heading/etc still diverse.
        pf = ParticleFilter(
            n_particles=40, config=minimal_config, rng=_rng(107),
            genesis_v_max_override=57.5,
            genesis_scenario_override=ScenarioFamily.SEVERE,
        )
        pf.initialize()
        lons = {round(p.state.longitude, 4) for p in pf.particles}
        assert len(lons) > 1

    def test_standalone_still_samples_per_particle(self, minimal_config):
        # No override -> scenarios drawn from the prior mix (not all identical
        # in general); Vmax varies across particles.
        pf = ParticleFilter(n_particles=40, config=minimal_config, rng=_rng(109))
        pf.initialize()
        vmaxes = {round(p.state.v_max_ms, 4) for p in pf.particles}
        assert len(vmaxes) > 1


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
