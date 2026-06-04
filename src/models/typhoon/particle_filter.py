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


__all__ = [
    "ParticleFilter",
    "systematic_resample",
]


# ===========================================================================
# Resampling — exposed at module level for direct testing
# ===========================================================================


def systematic_resample(weights: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Systematic resampling: pick N samples on a uniform grid offset by U.

    Returns indices into the original particle list. Each weight w_i is
    proportional to the expected number of times its index appears.

    Properties of systematic resampling vs multinomial:
    - Lower Monte Carlo variance for the same N.
    - Indices stay sorted (cheap memory access on contiguous arrays).
    - Reproducible under a single uniform draw.
    """
    n = len(weights)
    if n == 0:
        return np.empty(0, dtype=int)

    # Normalise defensively in case the caller passed unnormalised weights.
    total = float(np.sum(weights))
    if total <= 0.0:
        raise ValueError("systematic_resample requires positive total weight")
    w = np.asarray(weights, dtype=float) / total

    cum = np.cumsum(w)
    # Floating-point guard: ensure the last cumulant is exactly 1.0 so the
    # while-loop below cannot run off the end.
    cum[-1] = 1.0

    u0 = float(rng.uniform()) / n
    indices = np.zeros(n, dtype=int)
    j = 0
    for i in range(n):
        u = u0 + i / n
        while u > cum[j] and j < n - 1:
            j += 1
        indices[i] = j
    return indices


# ===========================================================================
# ParticleFilter
# ===========================================================================


class ParticleFilter:
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

    # ------------------------------------------------------------------
    # Top-level loop
    # ------------------------------------------------------------------

    def run_to_horizon(
        self,
        horizon_hours: Optional[float] = None,
        dt_hours: float = 1.0,
        plausibility_fn: Optional[
            Callable[[TyphoonParticle, Optional[TyphoonState]], float]
        ] = None,
        ess_threshold_frac: Optional[float] = None,
    ) -> List[TyphoonTrajectory]:
        """Propagate the filter to time horizon and return the trajectories.

        If initialize() has not been called, it runs automatically.

        Args:
            horizon_hours: simulation horizon. Defaults to config.horizon_hours.
            dt_hours: step length (hours).
            plausibility_fn: optional weight update function. If None, weights
                are not updated and resampling never triggers — the filter
                degenerates to a Monte Carlo ensemble.
            ess_threshold_frac: trigger resample when ESS < N * threshold_frac.
                Defaults to config.filter.ess_threshold_frac.

        Returns:
            List of TyphoonTrajectory, one per surviving particle, each
            containing the full state history from genesis to horizon.
        """
        if not self.particles:
            self.initialize()

        if horizon_hours is None:
            horizon_hours = self.config.horizon_hours
        if ess_threshold_frac is None:
            ess_threshold_frac = self.config.filter.ess_threshold_frac

        n_steps = int(round(horizon_hours / dt_hours))
        ess_threshold = self.n * ess_threshold_frac

        for _ in range(n_steps):
            self.propagate_one_step(dt_hours=dt_hours)
            if plausibility_fn is not None:
                self.compute_weights(plausibility_fn)
                if self.effective_sample_size() < ess_threshold:
                    self.resample()

        return self._extract_trajectories()

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _extract_trajectories(self) -> List[TyphoonTrajectory]:
        """Build TyphoonTrajectory objects from the recorded histories."""
        return [
            TyphoonTrajectory(
                event_id=f"EVT-{i:04d}",
                particle_id=self.particles[i].particle_id,
                scenario_family=self.scenarios[i],
                genesis_time=self.genesis_time,
                states=list(self.histories[i]),
            )
            for i in range(self.n)
        ]
