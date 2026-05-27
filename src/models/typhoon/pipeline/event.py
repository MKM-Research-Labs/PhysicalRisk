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

"""Single-event simulation: run the particle filter to horizon and evaluate
the wind-field along each particle's trajectory at every property point.
"""

from typing import Dict, List, Optional

import numpy as np

from config.typhoon import CatchmentTyphoonConfig
from models.typhoon.data_structures import WindFieldOutput
from models.typhoon.particle_filter import ParticleFilter
from models.typhoon.plausibility import make_particle_plausibility
from models.typhoon.wind_field import WindField


__all__ = ["simulate_one_event"]


def simulate_one_event(
    config: CatchmentTyphoonConfig,
    n_particles: int,
    rng: np.random.Generator,
    horizon_hours: Optional[float] = None,
    dt_hours: float = 1.0,
    use_plausibility: bool = True,
) -> Dict[str, List[WindFieldOutput]]:
    """Simulate one typhoon event and evaluate the wind-field at every property.

    Args:
        config: catchment configuration
        n_particles: number of particles in the SMC engine
        rng: random generator (advanced by the call)
        horizon_hours: simulation horizon; defaults to config.horizon_hours
        dt_hours: step length (hours)
        use_plausibility: if True, wire the simulation-mode plausibility
            adapter into the particle filter so weights track soft constraints

    Returns:
        Dict mapping property_id -> list of WindFieldOutput, one per
        particle. The list length equals n_particles for a given event.
    """
    plausibility_fn = make_particle_plausibility(config) if use_plausibility else None

    pf = ParticleFilter(n_particles=n_particles, config=config, rng=rng)
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

    return by_property
