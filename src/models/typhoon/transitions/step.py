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

"""Top-level one-step propagator and N-step advance().

Composes the four transition blocks (motion, position, wind, size) into a
single forward step. Order of operations is:

  1. Sample new motion (u_t, psi_t) using the regime-conditioned model.
  2. Advance position using the new motion.
  3. Evaluate the land flag at the new position.
  4. Update V_max conditional on the new land flag.
  5. Update (R_max, R_outer) conditional on the new V_max.

The regime is fixed at genesis in Phase 1 and is propagated unchanged.
"""

from typing import List

import numpy as np

from config.typhoon import CatchmentTyphoonConfig
from models.typhoon.data_structures import TyphoonState
from models.typhoon.transitions.motion import update_motion
from models.typhoon.transitions.position import update_position
from models.typhoon.transitions.size import update_size
from models.typhoon.transitions.wind import update_wind


__all__ = ["step", "advance"]


def step(
    state: TyphoonState,
    config: CatchmentTyphoonConfig,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> TyphoonState:
    """Advance the latent state by dt_hours.

    Args:
        state: previous latent state (time t-1)
        config: catchment configuration
        rng: random generator
        dt_hours: step length (hours), default 1.0

    Returns:
        New TyphoonState at time t.
    """
    new_speed, new_heading = update_motion(state, config.motion, rng, dt_hours)
    new_lon, new_lat = update_position(state, new_speed, new_heading, dt_hours)
    new_land_flag = bool(config.land_mask(new_lon, new_lat))
    new_v_max = update_wind(state, config.intensity, new_land_flag, rng, dt_hours)
    new_r_max, new_r_outer = update_size(state, new_v_max, config.size, rng, dt_hours)

    return TyphoonState(
        longitude=new_lon,
        latitude=new_lat,
        translation_speed_kmh=new_speed,
        heading_deg=new_heading,
        v_max_ms=new_v_max,
        r_max_km=new_r_max,
        r_outer_km=new_r_outer,
        regime=state.regime,
        land_flag=new_land_flag,
        time_hours=state.time_hours + dt_hours,
    )


def advance(
    state: TyphoonState,
    config: CatchmentTyphoonConfig,
    rng: np.random.Generator,
    n_steps: int,
    dt_hours: float = 1.0,
) -> List[TyphoonState]:
    """Apply step() n_steps times, returning the full forward trajectory.

    The returned list contains n_steps elements (the initial state is NOT
    included; callers that need the genesis state should prepend it).
    """
    if n_steps < 0:
        raise ValueError(f"n_steps must be non-negative, got {n_steps}")
    trajectory: List[TyphoonState] = []
    current = state
    for _ in range(n_steps):
        current = step(current, config, rng, dt_hours)
        trajectory.append(current)
    return trajectory
