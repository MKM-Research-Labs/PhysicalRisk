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

"""Size update — spec eq. (10).

Log-space mean-reverting update of (R_max, R_outer) toward a V-conditional
climatological target. The invariant R_max < R_outer is enforced
post-update by widening R_outer when collisions occur.
"""

import math
from typing import Tuple

import numpy as np

from config.typhoon import SizeParams
from models.typhoon.data_structures import TyphoonState


__all__ = ["update_size"]


def update_size(
    state: TyphoonState,
    new_v_max_ms: float,
    params: SizeParams,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> Tuple[float, float]:
    """Mean-reverting log-space update of (R_max, R_outer).

    Each radius is updated as:
        log(R_t) = log(R_{t-1})
                 + rate * dt * (log(R_target) - log(R_{t-1}))
                 + N(0, (sigma * sqrt(dt))^2)

    where log(R_target) is a linear function of log(V_max).
    """
    log_v = math.log(max(new_v_max_ms, 1.0))   # guard near zero
    log_rmax_target = params.r_max_intercept_log_km + params.r_max_v_coef * log_v
    log_router_target = params.r_outer_intercept_log_km + params.r_outer_v_coef * log_v

    log_rmax_prev = math.log(max(state.r_max_km, 1.0))
    log_router_prev = math.log(max(state.r_outer_km, 1.0))

    pull = params.mean_reversion_rate * dt_hours
    sigma_rmax = params.r_max_sigma_log * math.sqrt(dt_hours)
    sigma_router = params.r_outer_sigma_log * math.sqrt(dt_hours)

    log_rmax_new = (
        log_rmax_prev
        + pull * (log_rmax_target - log_rmax_prev)
        + float(rng.normal(0.0, sigma_rmax))
    )
    log_router_new = (
        log_router_prev
        + pull * (log_router_target - log_router_prev)
        + float(rng.normal(0.0, sigma_router))
    )

    r_max_new = math.exp(log_rmax_new)
    r_outer_new = math.exp(log_router_new)

    if r_outer_new <= r_max_new:
        r_outer_new = r_max_new * 1.5

    return r_max_new, r_outer_new
