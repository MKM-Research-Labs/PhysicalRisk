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
Storm duration sampler for the Storm Sequence Generator (MKM-SS-001 v3.0).

Triangular (min, mode, max) per intensity category, rounded to whole hours. The table
is ``config.port.STORM_DURATION_PARAMS``, read on every draw so that a
``storm_control.json`` override takes effect whenever it is applied.
"""

import numpy as np

import config.port as cp


def sample_duration(
    intensity_category: str,
    rng: np.random.RandomState = None,
) -> float:
    """Sample a storm duration in whole hours from the category's triangular law.

    Raises:
        ValueError: If intensity_category is not recognized.
    """
    params = cp.STORM_DURATION_PARAMS
    if intensity_category not in params:
        raise ValueError(
            f"Unknown intensity category: {intensity_category}. "
            f"Expected one of {list(params.keys())}"
        )

    low, mode, high = params[intensity_category]

    if rng is None:
        rng = np.random.RandomState()

    return round(rng.triangular(low, mode, high))


def get_max_duration(intensity_category: str) -> float:
    """Return the maximum possible duration for a category."""
    return cp.STORM_DURATION_PARAMS[intensity_category][2]


def get_duration_range(intensity_category: str) -> tuple:
    """Return (min, mode, max) duration tuple for a category."""
    return tuple(cp.STORM_DURATION_PARAMS[intensity_category])
