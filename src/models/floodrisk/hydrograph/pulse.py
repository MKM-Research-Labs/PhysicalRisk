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

"""Per-pulse gauge hydrograph builder."""

import numpy as np

from config.models import STORM_SIMULATION_HOURS
from .gamma import gamma_shape_array


def build_pulse_gauge_hydrograph(base_level: float, peak_m: float,
                                 start_hour: float, duration_hours: float,
                                 alpha: float,
                                 n_hours: int = STORM_SIMULATION_HOURS,
                                 ) -> np.ndarray:
    """Build a single-pulse hydrograph at the gauge using the gamma template.

    WSE_i(h) = base + (peak - base) * phi((h - start) / duration)

    Args:
        base_level: Gauge base water level (m AOD).
        peak_m: Pulse peak water surface elevation (m AOD).
        start_hour: Pulse start hour within the 168h window.
        duration_hours: Pulse duration (hours).
        alpha: Gamma shape parameter for this storm type.
        n_hours: Total simulation hours (default 168).

    Returns:
        np.ndarray of shape (n_hours,) with WSE values.
    """
    hours = np.arange(n_hours, dtype=float)
    shape = gamma_shape_array(hours, start_hour, duration_hours, alpha)
    exceedance = max(0.0, peak_m - base_level)
    return base_level + exceedance * shape
