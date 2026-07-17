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

"""
Transition layer for the typhoon model.

Composes the four transition blocks from the Bayesian typhoon progression
specification:

  - compass.py  — circular-arithmetic helpers
  - position.py — equirectangular advection (spec eqs. 6-7)
  - motion.py   — regime-conditioned motion update (spec eq. 5)
  - wind.py     — over-water drift / over-land decay (spec eqs. 8-9)
  - size.py     — log-space mean-reverting (R_max, R_outer) (spec eq. 10)
  - step.py     — one-step propagator and N-step advance()

The public surface is re-exported here so callers (and tests) continue to
write ``from models.typhoon.transitions import step, update_motion, ...``.
Each transition block can be evolved independently in its own submodule;
this aggregator only needs touching when public symbols change.
"""

from models.typhoon.transitions.compass import (
    signed_compass_delta,
    wrap_compass_degrees,
)
from models.typhoon.transitions.motion import (
    RECURVATURE_REGIMES,
    update_motion,
)
from models.typhoon.transitions.position import (
    EARTH_RADIUS_KM,
    haversine_step,
    update_position,
)
from models.typhoon.transitions.size import update_size
from models.typhoon.transitions.step import advance, step
from models.typhoon.transitions.wind import update_wind


__all__ = [
    # compass
    "wrap_compass_degrees",
    "signed_compass_delta",
    # position
    "EARTH_RADIUS_KM",
    "haversine_step",
    "update_position",
    # motion
    "RECURVATURE_REGIMES",
    "update_motion",
    # wind
    "update_wind",
    # size
    "update_size",
    # step
    "step",
    "advance",
]
