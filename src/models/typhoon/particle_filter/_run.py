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

"""Particle filter top-level loop and trajectory extraction."""

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


class _RunMixin:
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
