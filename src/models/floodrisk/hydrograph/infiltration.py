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

"""Flow-path infiltration loss model."""

import numpy as np

from config.models import (
    INFILTRATION_RATE_PER_HOUR,
    INFILTRATION_YMAX_REF_M,
    DEFAULT_IMPERV_FRACTION,
)


def apply_infiltration(raw_depth: np.ndarray,
                       kappa: float = INFILTRATION_RATE_PER_HOUR,
                       y_max: float = INFILTRATION_YMAX_REF_M,
                       f_imperv: float = DEFAULT_IMPERV_FRACTION,
                       dt: float = 1.0) -> np.ndarray:
    """Apply time-varying infiltration loss to a depth series.

    Tracks cumulative infiltrated depth Y_inf.  Infiltration capacity
    decreases as the soil saturates.  The fraction of water *lost* to
    infiltration at each step is proportional to remaining capacity:

        loss(t) = min(kappa * raw_depth * dt,  Y_max - Y_inf)
        depth(t) = raw_depth(t) - loss(t)

    Once Y_inf reaches Y_max the ground is fully saturated and all
    subsequent water passes through unchanged.

    Y_max = (1 - f_imperv) * y_max_ref.

    Args:
        raw_depth: Raw flood depth above ground (m), shape (n_hours,).
        kappa: Hourly infiltration rate constant (1/hr).
        y_max: Reference max infiltrable depth for fully pervious (m).
        f_imperv: Fraction impervious surface (0-1).
        dt: Time step in hours.

    Returns:
        Adjusted depth array, same shape as input.
    """
    effective_ymax = (1.0 - f_imperv) * y_max
    if effective_ymax <= 0 or kappa <= 0:
        # Fully impervious or no infiltration → no loss
        return raw_depth.copy()

    result = np.empty_like(raw_depth)
    y_inf = 0.0

    for i in range(len(raw_depth)):
        d = raw_depth[i]
        if d > 0 and y_inf < effective_ymax:
            # Infiltration loss limited by remaining capacity
            loss = min(kappa * d * dt, effective_ymax - y_inf)
            y_inf += loss
            result[i] = max(0.0, d - loss)
        else:
            # Ground saturated or no water — pass through
            result[i] = d

    return result
