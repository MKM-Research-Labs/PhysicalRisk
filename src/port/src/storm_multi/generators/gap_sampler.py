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
Inter-storm gap sampler for the Storm Sequence Generator (MKM-SS-001 v3.0).

Gaps must be long enough to show observable river level decline between storms. The
gap type follows the sequence type; its triangular (min, mode, max) is
``config.port.STORM_GAP_PARAMS``, read on every draw so a ``storm_control.json``
override takes effect whenever it is applied. The minimum is also the shortest gap a
sequence may have: the sequence generator reserves it before capping durations.
"""

import numpy as np

import config.port as cp

from ..core.data_structures import SEQUENCE_GAP_TYPE, SequenceType


def get_gap_range(sequence_type: SequenceType) -> tuple:
    """Return (min, mode, max) gap parameters for a sequence type."""
    if sequence_type == SequenceType.ISOLATED:
        return (0, 0, 0)
    return tuple(cp.STORM_GAP_PARAMS[SEQUENCE_GAP_TYPE[sequence_type].value])


def get_min_gap(sequence_type: SequenceType) -> float:
    """The shortest gap a sequence of this type may have (0 for isolated)."""
    return get_gap_range(sequence_type)[0]


def sample_gap(
    sequence_type: SequenceType,
    rng: np.random.RandomState = None,
) -> float:
    """Sample an inter-storm gap for a given sequence type, in whole hours.

    Physical interpretation:
      - Medium gaps (24-72h): river levels drop 30-60% from Storm 1 peak
      - Short gaps (6-36h): minimal drainage, high compounding risk
    """
    if sequence_type == SequenceType.ISOLATED:
        return 0.0

    low, mode, high = get_gap_range(sequence_type)

    if rng is None:
        rng = np.random.RandomState()

    return round(rng.triangular(low, mode, high))
