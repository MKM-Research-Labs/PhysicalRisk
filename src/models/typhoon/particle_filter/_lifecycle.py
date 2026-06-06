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

"""Particle filter lifecycle: genesis sampling and propagation."""

from datetime import datetime
from typing import Callable, List, Optional

import numpy as np

from config.typhoon import CatchmentTyphoonConfig, ScenarioFamily
from models.typhoon.data_structures import (
    TyphoonParticle,
    TyphoonState,
    TyphoonTrajectory,
)
from models.typhoon.genesis import sample_genesis, sample_scenario_family
from models.typhoon.transitions import step


class _LifecycleMixin:
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Sample N genesis particles with uniform weights.

        Each particle draws its own scenario family from the prior mix and
        a genesis state conditioned on that scenario. Scenario is retained
        on the filter so trajectories can report the family that seeded
        them, including across resampling generations.
        """
        mix = self.config.genesis_prior.scenario_mix
        uniform = 1.0 / self.n
        coupled = self.genesis_v_max_override is not None
        particles: List[TyphoonParticle] = []
        histories: List[List[TyphoonState]] = []
        scenarios: List[ScenarioFamily] = []
        for i in range(self.n):
            if coupled:
                # Coupled mode: genesis Vmax and scenario label are fixed for
                # the event; only the non-intensity genesis dimensions vary.
                scenario = self.genesis_scenario_override
                state = sample_genesis(
                    self.config, scenario, self.rng,
                    v_max_override=self.genesis_v_max_override,
                )
            else:
                scenario = sample_scenario_family(mix, self.rng)
                state = sample_genesis(self.config, scenario, self.rng)
            particles.append(TyphoonParticle(
                state=state,
                weight=uniform,
                particle_id=i,
                parent_id=None,
            ))
            histories.append([state])
            scenarios.append(scenario)
        self.particles = particles
        self.histories = histories
        self.scenarios = scenarios
        self.step_count = 0

    # ------------------------------------------------------------------
    # Propagation
    # ------------------------------------------------------------------

    def propagate_one_step(self, dt_hours: float = 1.0) -> None:
        """Apply transitions.step to every particle.

        Weights are unchanged by propagation. Histories grow by one state
        per particle. Particle IDs are preserved across propagation (only
        resample mutates them).
        """
        if not self.particles:
            raise RuntimeError("Particle filter not initialised — call initialize() first")
        new_particles: List[TyphoonParticle] = []
        for p in self.particles:
            new_state = step(p.state, self.config, self.rng, dt_hours=dt_hours)
            new_particles.append(TyphoonParticle(
                state=new_state,
                weight=p.weight,
                particle_id=p.particle_id,
                parent_id=p.parent_id,
            ))
        self.particles = new_particles
        for i, p in enumerate(new_particles):
            self.histories[i].append(p.state)
        self.step_count += 1
