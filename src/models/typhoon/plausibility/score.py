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

"""Plausibility composer and ParticleFilter adapter.

The composer plausibility_score multiplies the four component scores into
a single value in (0, 1]. The adapter make_particle_plausibility wraps
the composer into the (particle, prev_state) signature consumed by the
particle filter's compute_weights method.
"""

from typing import Callable, Optional

from config.typhoon import CatchmentTyphoonConfig
from models.typhoon.data_structures import TyphoonParticle, TyphoonState
from models.typhoon.plausibility.basin_boundary import basin_boundary_score
from models.typhoon.plausibility.heading_jump import heading_jump_score
from models.typhoon.plausibility.regime_consistency import regime_consistency_score
from models.typhoon.plausibility.speed_jump import speed_jump_score


__all__ = ["plausibility_score", "make_particle_plausibility"]


def plausibility_score(
    state: TyphoonState,
    prev_state: TyphoonState,
    config: CatchmentTyphoonConfig,
) -> float:
    """Composite plausibility score in (0, 1] for the transition prev_state -> state.

    Each weight in config.plausibility independently scales one component.
    Setting any weight to zero disables that component.

    The basin bbox is taken from config.genesis_prior.bbox in Phase 1; a
    later phase may add a wider explicit basin region to PlausibilityWeights.
    """
    weights = config.plausibility
    bbox = config.genesis_prior.bbox
    motion = config.motion

    s1 = heading_jump_score(state, prev_state, weights.heading_jump_weight, weights.heading_jump_sigma_deg)
    s2 = speed_jump_score(state, prev_state, weights.speed_jump_weight, weights.speed_jump_sigma_kmh)
    s3 = basin_boundary_score(state, bbox, weights.basin_boundary_weight)
    s4 = regime_consistency_score(state, motion, weights.regime_consistency_weight)

    return s1 * s2 * s3 * s4


def make_particle_plausibility(
    config: CatchmentTyphoonConfig,
) -> Callable[[TyphoonParticle, Optional[TyphoonState]], float]:
    """Adapter for ParticleFilter.compute_weights.

    Returns a callable matching the (particle, prev_state) signature the
    particle filter expects. If prev_state is None (called before any
    propagation has happened), returns 1.0 — no penalty can be defined.
    """
    def fn(particle: TyphoonParticle, prev_state: Optional[TyphoonState]) -> float:
        if prev_state is None:
            return 1.0
        return plausibility_score(particle.state, prev_state, config)
    return fn
