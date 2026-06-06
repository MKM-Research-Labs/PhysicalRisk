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

"""Particle filter weighting and resampling."""

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

from models.typhoon.particle_filter._resample import systematic_resample


class _WeightsMixin:
    # ------------------------------------------------------------------
    # Weights and resampling
    # ------------------------------------------------------------------

    def compute_weights(
        self,
        plausibility_fn: Callable[[TyphoonParticle, Optional[TyphoonState]], float],
    ) -> None:
        """Multiply each weight by a plausibility score and renormalise.

        plausibility_fn(particle, prev_state) returns a non-negative scalar.
        prev_state is the previous step's state for that particle (taken
        from the recorded history) or None if the filter has not yet
        propagated (history contains only the genesis state).

        If the product collapses to zero (every particle invalid), weights
        are reset to uniform to keep the simulation alive.
        """
        scores_list = []
        for i, p in enumerate(self.particles):
            history = self.histories[i]
            prev_state: Optional[TyphoonState] = history[-2] if len(history) >= 2 else None
            scores_list.append(float(plausibility_fn(p, prev_state)))
        scores = np.array(scores_list, dtype=float)
        if np.any(scores < 0):
            raise ValueError("Plausibility scores must be non-negative")

        weights = np.array([p.weight for p in self.particles], dtype=float)
        new_w = weights * scores
        total = float(new_w.sum())
        if total <= 0.0:
            new_w = np.full(self.n, 1.0 / self.n, dtype=float)
        else:
            new_w = new_w / total

        for i, p in enumerate(self.particles):
            self.particles[i] = TyphoonParticle(
                state=p.state,
                weight=float(new_w[i]),
                particle_id=p.particle_id,
                parent_id=p.parent_id,
            )

    def effective_sample_size(self) -> float:
        """ESS = 1 / sum(w_i^2). Equals N for uniform weights, 1 for a delta."""
        w = np.array([p.weight for p in self.particles], dtype=float)
        denom = float(np.sum(w * w))
        if denom <= 0.0:
            return 0.0
        return 1.0 / denom

    def resample(self) -> None:
        """Systematic resampling. Resets weights to 1/N and rebuilds histories.

        The new particle_id sequence is 0..N-1 (filter generation); the
        parent_id points back to the source particle so callers can trace
        ancestry across resampling generations.
        """
        weights = np.array([p.weight for p in self.particles], dtype=float)
        indices = systematic_resample(weights, self.rng)

        uniform = 1.0 / self.n
        new_particles: List[TyphoonParticle] = []
        new_histories: List[List[TyphoonState]] = []
        new_scenarios: List[ScenarioFamily] = []
        for new_i, src_i in enumerate(indices):
            src = self.particles[src_i]
            new_particles.append(TyphoonParticle(
                state=src.state,
                weight=uniform,
                particle_id=new_i,
                parent_id=src.particle_id,
            ))
            # Copy the history so divergent futures don't share state.
            new_histories.append(list(self.histories[src_i]))
            new_scenarios.append(self.scenarios[src_i])

        self.particles = new_particles
        self.histories = new_histories
        self.scenarios = new_scenarios
