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

"""Speed-jump plausibility — penalise implausible translation-speed changes.

Gaussian penalty on |Δu| between consecutive states:

    score = exp(-weight * (|Δu| / sigma_kmh)^2)

Setting weight=0 or sigma_kmh<=0 disables the penalty (score = 1.0).
"""

import math

from models.typhoon.data_structures import TyphoonState


__all__ = ["speed_jump_score"]


def speed_jump_score(
    state: TyphoonState,
    prev_state: TyphoonState,
    weight: float,
    sigma_kmh: float,
) -> float:
    """Return a multiplier in (0, 1] penalising large translation-speed jumps."""
    if weight <= 0.0 or sigma_kmh <= 0.0:
        return 1.0
    delta = abs(state.translation_speed_kmh - prev_state.translation_speed_kmh)
    z = delta / sigma_kmh
    return math.exp(-weight * z * z)
