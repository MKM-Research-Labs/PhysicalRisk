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

"""Antecedent saturation and pulse superposition."""

import math
from typing import List, Optional

import numpy as np

from config.models import (
    SATURATION_BETA,
    SATURATION_P0_MM,
    STORM_SIMULATION_HOURS,
)


def compute_saturation_factor(antecedent_precip_mm: float,
                              beta: float = SATURATION_BETA,
                              p0: float = SATURATION_P0_MM) -> float:
    """Compute saturation multiplier for a pulse's peak exceedance.

    s_i = 1 + beta * log(1 + A_i / P_0)

    Later pulses in a sequence get amplified because earlier rainfall
    has saturated the catchment.

    Args:
        antecedent_precip_mm: Cumulative precipitation from prior pulses (mm).
        beta: Log-sensitivity parameter (default 0.2).
        p0: Reference precipitation (mm, default 50).

    Returns:
        Multiplier >= 1.0.
    """
    if antecedent_precip_mm <= 0 or p0 <= 0:
        return 1.0
    return 1.0 + beta * math.log(1.0 + antecedent_precip_mm / p0)


def superimpose_pulses(base_level: float,
                       pulse_arrays: List[np.ndarray],
                       cap: Optional[float] = None) -> np.ndarray:
    """Superimpose multiple pulse hydrographs via linear addition.

    WSE(h) = base + sum_i (pulse_i(h) - base)

    Args:
        base_level: Gauge base water level (m AOD).
        pulse_arrays: List of per-pulse WSE arrays (each shape (n_hours,)).
        cap: Optional absolute cap on exceedance above base (m).

    Returns:
        Combined WSE array of same shape as input arrays.
    """
    if not pulse_arrays:
        n = STORM_SIMULATION_HOURS
        return np.full(n, base_level)

    n = len(pulse_arrays[0])
    total_exceedance = np.zeros(n, dtype=float)
    for arr in pulse_arrays:
        total_exceedance += np.maximum(0.0, arr - base_level)

    if cap is not None and cap > 0:
        np.clip(total_exceedance, 0, cap, out=total_exceedance)

    return base_level + total_exceedance
