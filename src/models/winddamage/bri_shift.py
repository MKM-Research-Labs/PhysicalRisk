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

"""BRI-driven shift of the wind-damage curve's v_50 threshold.

Direct analogue of `bri_stilt` in floodrisk/depth_damage.py — same
log-aggregated structure, units in m/s instead of metres:

    shift = BRI_WIND_ALPHA_MS    · ln(bri_wind      / BRI_WIND_REFERENCE)
          + BRI_COMPOSITE_BETA_MS · ln(bri_composite / BRI_COMPOSITE_REFERENCE)

The result is signed and capped at ±WIND_V50_SHIFT_MAX_MS. Positive shifts
translate the damage curve rightward (the property tolerates higher winds
before damage); negative shifts translate it leftward (the property is
more vulnerable than baseline).
"""

import math

from config.bri import (
    BRI_COMPOSITE_BETA_MS,
    BRI_COMPOSITE_REFERENCE,
    BRI_WIND_ALPHA_MS,
    BRI_WIND_REFERENCE,
    LN_FLOOR,
    WIND_V50_SHIFT_MAX_MS,
)


__all__ = ["bri_v50_shift"]


def bri_v50_shift(bri_wind_score: float, bri_composite_score: float) -> float:
    """Signed shift in m/s applied to v_50 (the 50%-damage gust threshold).

    Args:
        bri_wind_score:     BRIWindScore in [0, 1] from the resilience CDM.
        bri_composite_score: BRIScore (composite) in [0, 1] from the resilience CDM.

    Returns:
        Signed shift in m/s, capped to ±WIND_V50_SHIFT_MAX_MS.
    """
    wind_term = BRI_WIND_ALPHA_MS * math.log(
        max(bri_wind_score, LN_FLOOR) / BRI_WIND_REFERENCE
    )
    composite_term = BRI_COMPOSITE_BETA_MS * math.log(
        max(bri_composite_score, LN_FLOOR) / BRI_COMPOSITE_REFERENCE
    )
    raw = wind_term + composite_term
    return max(-WIND_V50_SHIFT_MAX_MS, min(WIND_V50_SHIFT_MAX_MS, raw))
