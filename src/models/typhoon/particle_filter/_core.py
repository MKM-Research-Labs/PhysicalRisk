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

"""
Hand-rolled Sequential Monte Carlo (particle filter) engine.

Implements the SMC representation from the Bayesian typhoon progression
spec, eq. (13):

    p(s_t | y_{1:t}) ~= sum_i w_t^(i) * delta(s_t - s_t^(i))

The engine drives Phase 1's pure-simulation mode: no real observations,
soft plausibility scores only. Defaults are deliberately *loose* — low
ESS threshold for resampling — so the posterior preserves trajectory
breadth, which is the Phase 1 priority.

Per-particle loop implementation. Each particle's state is advanced via
the standard transitions.step() function so the filter's numerical
behaviour matches the unit-tested transition layer exactly. Vectorisation
over particles is a future optimisation that can be added without
changing the API.

Public surface:
    ParticleFilter        — the SMC engine
    systematic_resample   — index sampler (exposed for testing)

Usage:
    rng = np.random.default_rng(seed)
    pf = ParticleFilter(n_particles=1000, config=cfg, rng=rng)
    pf.initialize()
    trajectories = pf.run_to_horizon(horizon_hours=168.0)
"""

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
from models.typhoon.particle_filter._lifecycle import _LifecycleMixin
from models.typhoon.particle_filter._weights import _WeightsMixin
from models.typhoon.particle_filter._run import _RunMixin


__all__ = [
    "ParticleFilter",
    "systematic_resample",
]


class ParticleFilter(_LifecycleMixin, _WeightsMixin, _RunMixin):
    """Sequential Monte Carlo posterior approximation over typhoon states.

    Attributes available after initialize():
        particles: list[TyphoonParticle] — current weighted particles
        histories: list[list[TyphoonState]] — per-particle trajectory so far
        scenarios: list[ScenarioFamily] — scenario family used at genesis per particle
        step_count: int — number of propagate_one_step calls since init
    """

    def __init__(
        self,
        n_particles: int,
        config: CatchmentTyphoonConfig,
        rng: np.random.Generator,
        genesis_time: Optional[datetime] = None,
        genesis_v_max_override: Optional[float] = None,
        genesis_scenario_override: Optional[ScenarioFamily] = None,
    ):
        if n_particles <= 0:
            raise ValueError(f"n_particles must be positive, got {n_particles}")
        self.n: int = n_particles
        self.config: CatchmentTyphoonConfig = config
        self.rng: np.random.Generator = rng
        # Genesis time is metadata for the output trajectories; it does not
        # affect sampling. Pinned default keeps tests reproducible.
        self.genesis_time: datetime = genesis_time or datetime(2026, 1, 1)

        # Storm->wind coupling (coupling_spec.md §4): when set, every particle
        # initialises at this peak wind and scenario label rather than drawing
        # an independent scenario + Vmax. The event's windiness is fixed by the
        # paired storm; the filter still explores track/size/location/regime.
        self.genesis_v_max_override: Optional[float] = genesis_v_max_override
        self.genesis_scenario_override: Optional[ScenarioFamily] = genesis_scenario_override

        self.particles: List[TyphoonParticle] = []
        self.histories: List[List[TyphoonState]] = []
        self.scenarios: List[ScenarioFamily] = []
        self.step_count: int = 0
