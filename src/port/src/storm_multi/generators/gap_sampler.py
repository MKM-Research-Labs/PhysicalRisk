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
Inter-storm gap sampler for Storm Generator v2.0.

Gaps must be long enough to show observable river level decline
between storms. Gap type varies by sequence type to create different
drainage patterns.
"""

import numpy as np

from ..core.data_structures import GapType, SequenceType, SEQUENCE_GAP_TYPE

# Inter-storm gap parameters — spec Section 3.2
# (min_hours, mode_hours, max_hours) — triangular distribution
GAP_PARAMS = {
    GapType.SHORT: (6, 18, 36),      # Minimal drainage
    GapType.MEDIUM: (24, 48, 72),     # Partial drainage
    GapType.LONG: (48, 96, 144),      # Substantial drainage
}


def sample_gap(
    sequence_type: SequenceType,
    rng: np.random.RandomState = None,
) -> float:
    """Sample an inter-storm gap for a given sequence type.

    Physical interpretation:
      - Medium gaps (24-72h): river levels drop 30-60% from Storm 1 peak
      - Short gaps (6-36h): minimal drainage, high compounding risk
      - Long gaps (48-144h): 60-80% recovery toward baseline

    Args:
        sequence_type: Type of sequence (determines gap category).
        rng: Random state for reproducibility.

    Returns:
        Gap duration in hours (rounded to nearest integer).
    """
    if sequence_type == SequenceType.ISOLATED:
        return 0.0

    gap_type = SEQUENCE_GAP_TYPE[sequence_type]
    low, mode, high = GAP_PARAMS[gap_type]

    if rng is None:
        rng = np.random.RandomState()

    return round(rng.triangular(low, mode, high))


def get_gap_range(sequence_type: SequenceType) -> tuple:
    """Return (min, mode, max) gap parameters for a sequence type."""
    if sequence_type == SequenceType.ISOLATED:
        return (0, 0, 0)
    gap_type = SEQUENCE_GAP_TYPE[sequence_type]
    return GAP_PARAMS[gap_type]
