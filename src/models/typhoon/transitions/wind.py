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

"""Wind intensity update — spec eqs. (8) and (9).

Two-mode update:

  Over water (eq. 8): V_t ~ N(V_{t-1} + drift * dt, (sigma * sqrt(dt))^2)
  Over land  (eq. 9): V_t = V_{t-1} * exp(-k_land * dt)

The end-of-step land flag is used (the wind responds to where the storm
now sits, not where it sat at the start of the step).
"""

import math

import numpy as np

from config.typhoon import IntensityParams
from models.typhoon.data_structures import TyphoonState


__all__ = ["update_wind"]


def update_wind(
    state: TyphoonState,
    params: IntensityParams,
    land_flag: bool,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> float:
    """Update V_max given the (end-of-step) land flag.

    Result is clamped to [0, +inf).
    """
    if land_flag:
        v_new = state.v_max_ms * math.exp(-params.k_land_per_hour * dt_hours)
    else:
        mean = state.v_max_ms + params.drift_ms_per_hour * dt_hours
        std = params.sigma_ms_per_hour * math.sqrt(dt_hours)
        v_new = float(rng.normal(mean, std))
    return max(0.0, v_new)
