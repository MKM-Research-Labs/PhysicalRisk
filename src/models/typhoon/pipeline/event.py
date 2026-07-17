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

"""Single-event simulation: run the particle filter to horizon and evaluate
the wind-field along each particle's trajectory at every property point.
"""

from typing import Dict, List, NamedTuple, Optional

import numpy as np

from config.typhoon import CatchmentTyphoonConfig
from models.typhoon.data_structures import TyphoonTrajectory, WindFieldOutput
from models.typhoon.particle_filter import ParticleFilter
from models.typhoon.plausibility import make_particle_plausibility
from models.typhoon.wind_field import WindField


__all__ = [
    "EventResult",
    "simulate_one_event",
    "pick_representative_index",
    "pick_representative_trajectory",
]


class EventResult(NamedTuple):
    """One event's outputs.

    Attributes:
        by_property: property_id -> list of WindFieldOutput (one per particle)
        trajectories: list of TyphoonTrajectory (one per particle)
    """
    by_property: Dict[str, List[WindFieldOutput]]
    trajectories: List[TyphoonTrajectory]


def simulate_one_event(
    config: CatchmentTyphoonConfig,
    n_particles: int,
    rng: np.random.Generator,
    horizon_hours: Optional[float] = None,
    dt_hours: float = 1.0,
    use_plausibility: bool = True,
    genesis_v_max: Optional[float] = None,
    genesis_scenario=None,
) -> EventResult:
    """Simulate one typhoon event and evaluate the wind-field at every property.

    Args:
        config: catchment configuration
        n_particles: number of particles in the SMC engine
        rng: random generator (advanced by the call)
        horizon_hours: simulation horizon; defaults to config.horizon_hours
        dt_hours: step length (hours)
        use_plausibility: if True, wire the simulation-mode plausibility
            adapter into the particle filter so weights track soft constraints
        genesis_v_max: storm->wind coupling override (coupling_spec.md §4) —
            when set, every particle's genesis peak wind is fixed to this
            value (the event's windiness, set by the paired storm severity)
            rather than drawn independently per particle.
        genesis_scenario: derived scenario-family label that accompanies the
            coupled Vmax (used only for trajectory tagging).

    Returns:
        EventResult bundling the wind-field outputs per property and the
        underlying particle trajectories. Callers that only need the wind
        outputs read result.by_property; callers that want to inspect the
        actual storm tracks read result.trajectories.
    """
    plausibility_fn = make_particle_plausibility(config) if use_plausibility else None

    pf = ParticleFilter(
        n_particles=n_particles, config=config, rng=rng,
        genesis_v_max_override=genesis_v_max,
        genesis_scenario_override=genesis_scenario,
    )
    trajectories = pf.run_to_horizon(
        horizon_hours=horizon_hours,
        dt_hours=dt_hours,
        plausibility_fn=plausibility_fn,
    )

    wind_field = WindField(config)

    by_property: Dict[str, List[WindFieldOutput]] = {p.property_id: [] for p in config.property_points}
    for trajectory in trajectories:
        for prop in config.property_points:
            wf_output = wind_field.evaluate_trajectory(trajectory, prop)
            by_property[prop.property_id].append(wf_output)

    return EventResult(by_property=by_property, trajectories=trajectories)


def pick_representative_index(
    trajectories: List[TyphoonTrajectory],
) -> Optional[int]:
    """Return the index of the trajectory whose peak V_max sits closest to the median.

    None if the input is empty. Splitting the index-picking from the
    trajectory-returning lets callers reuse the same representative
    index against parallel lists (e.g. per-particle wind outputs).
    """
    if not trajectories:
        return None
    peaks = np.array([max(s.v_max_ms for s in t.states) for t in trajectories])
    median_peak = float(np.median(peaks))
    return int(np.argmin(np.abs(peaks - median_peak)))


def pick_representative_trajectory(
    trajectories: List[TyphoonTrajectory],
) -> Optional[TyphoonTrajectory]:
    """Pick the trajectory whose peak V_max sits closest to the median.

    A simple "central tendency" choice for inspection / visualisation —
    avoids picking the outlier with the strongest winds, gives a
    representative storm track for the event.
    """
    idx = pick_representative_index(trajectories)
    if idx is None:
        return None
    return trajectories[idx]
