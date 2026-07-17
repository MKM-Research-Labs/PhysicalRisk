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

"""Track-regime / scenario-family enums and the LandMask type alias."""

from enum import Enum
from typing import Callable


class RegimeClass(Enum):
    """Discrete track regime — spec p.3.

    The regime conditions the motion transition model. In Phase 1 the regime
    is sampled at genesis and held fixed for the event (spec p.4).
    """
    STRAIGHT_WESTWARD = "straight_westward"
    NW_RECURVER = "nw_recurver"
    SHARP_RECURVE = "sharp_recurve"
    STALLED = "stalled"
    LANDFALL_DECAY = "landfall_decay"


class ScenarioFamily(Enum):
    """Stress-scenario family — spec p.10.

    Scenario family drives peak-wind distribution params (mu, sigma, v_T, alpha),
    size distribution shape, regime priors, and persistence/decay.
    """
    HISTORICAL = "historical"
    BASELINE = "baseline"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


# ===========================================================================
# Type aliases
# ===========================================================================


# A land mask is a callable taking (longitude, latitude) -> True if land.
# Catchments supply this; the model never embeds geometry.
LandMask = Callable[[float, float], bool]
