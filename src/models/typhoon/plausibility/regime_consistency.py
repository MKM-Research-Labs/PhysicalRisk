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

"""Regime-consistency plausibility — penalise off-regime speed/heading.

For each regime, the catchment's MotionParams supply a climatological
mean and sigma for translation speed and heading. A state's deviation
from those means (in standardised units) accumulates into a Gaussian
penalty:

    z_u    = (u - mean_u[k]) / sigma_u[k]
    z_psi  = signed_compass_delta(psi, mean_psi[k]) / sigma_psi[k]
    score  = exp(-weight * (z_u^2 + z_psi^2))

The spec example — "STALLED regime should have low u; penalise if u
stays high" — falls out naturally: STALLED has a small mean_speed and
small sigma_speed, so a fast-moving state produces a large z_u.

If a regime's sigma is zero or missing, that dimension is treated as
disabled (z = 0 for that axis).
"""

import math

from config.typhoon import MotionParams
from models.typhoon.data_structures import TyphoonState
from models.typhoon.transitions.compass import signed_compass_delta


__all__ = ["regime_consistency_score"]


def regime_consistency_score(
    state: TyphoonState,
    motion: MotionParams,
    weight: float,
) -> float:
    """Return a multiplier in (0, 1] penalising off-regime behaviour."""
    if weight <= 0.0:
        return 1.0

    regime = state.regime
    expected_speed = motion.mean_speed_kmh.get(regime)
    expected_heading = motion.mean_heading_deg.get(regime)
    sigma_speed = motion.sigma_speed_kmh.get(regime, 0.0)
    sigma_heading = motion.sigma_heading_deg.get(regime, 0.0)

    if expected_speed is None or expected_heading is None:
        # Regime not configured in this catchment; no penalty.
        return 1.0

    z_speed = 0.0
    if sigma_speed > 0.0:
        z_speed = (state.translation_speed_kmh - expected_speed) / sigma_speed

    z_heading = 0.0
    if sigma_heading > 0.0:
        delta = signed_compass_delta(state.heading_deg, expected_heading)
        z_heading = delta / sigma_heading

    composite = z_speed * z_speed + z_heading * z_heading
    return math.exp(-weight * composite)
