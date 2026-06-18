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

"""Motion update — spec eq. (5).

Regime-conditioned Gaussian update on translation speed and heading, with
persistence around the previous step plus an optional northward
recurvature bias above the configured latitude threshold.
"""

import math
from typing import Tuple

import numpy as np

from config.typhoon import MotionParams
from models.typhoon.data_structures import RegimeClass, TyphoonState
from models.typhoon.transitions.compass import (
    signed_compass_delta,
    wrap_compass_degrees,
)


__all__ = [
    "RECURVATURE_REGIMES",
    "update_motion",
]


# Regimes that apply a northward recurvature bias when above the
# recurvature latitude. SHARP_RECURVE is included because by definition
# it implies a steeper northward turn at the recurvature latitude.
RECURVATURE_REGIMES = frozenset({RegimeClass.NW_RECURVER, RegimeClass.SHARP_RECURVE})


def update_motion(
    state: TyphoonState,
    params: MotionParams,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> Tuple[float, float]:
    """Sample the next translation speed and heading.

    Applies persistence-plus-regime-target means, then adds Gaussian noise.
    Above the recurvature latitude, NW_RECURVER and SHARP_RECURVE regimes
    apply an additive northward bias bounded by recurvature_bias_deg_per_step.

    Args:
        state: current latent state
        params: catchment motion parameters
        rng: random generator
        dt_hours: step length (hours). Noise variance scales linearly with dt
            so std scales with sqrt(dt).

    Returns:
        (new_speed_kmh, new_heading_deg)
    """
    regime = state.regime

    # --- Speed: persistence around regime climatological mean ---
    mean_speed = params.mean_speed_kmh[regime]
    sigma_speed = params.sigma_speed_kmh[regime] * math.sqrt(dt_hours)
    mu_u = params.speed_persistence * state.translation_speed_kmh + (
        1.0 - params.speed_persistence
    ) * mean_speed
    new_speed = float(rng.normal(mu_u, sigma_speed))
    # Speed must be non-negative; a reverse-moving storm is unphysical here.
    new_speed = max(0.0, new_speed)

    # --- Heading: circular persistence + optional recurvature bias ---
    mean_heading = params.mean_heading_deg[regime]
    # Apply persistence using a signed-delta toward the regime mean so we
    # don't accidentally short-cross the compass seam (e.g. 350 -> 10).
    delta_to_target = signed_compass_delta(mean_heading, state.heading_deg)
    mu_psi = state.heading_deg + (1.0 - params.heading_persistence) * delta_to_target

    # Recurvature bias: pull heading toward 0 (north) when conditions met.
    if regime in RECURVATURE_REGIMES and state.latitude > params.recurvature_latitude:
        delta_to_north = signed_compass_delta(0.0, mu_psi)
        bias_step = min(abs(delta_to_north), params.recurvature_bias_deg_per_step * dt_hours)
        if delta_to_north != 0.0:
            mu_psi = mu_psi + math.copysign(bias_step, delta_to_north)

    sigma_heading = params.sigma_heading_deg[regime] * math.sqrt(dt_hours)
    new_heading = float(rng.normal(mu_psi, sigma_heading))
    new_heading = wrap_compass_degrees(new_heading)

    return new_speed, new_heading
