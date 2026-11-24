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
Intensity sampler for the Storm Sequence Generator (MKM-SS-001 v3.0).

Controls whether a storm becomes part of a sequence, what type of sequence, how many
storms, and the correlated intensity relationship between successive storms. Every
parameter is read from ``config.port`` on each call, so a ``storm_control.json``
override takes effect whenever it is applied, whatever was imported first.
"""


import numpy as np

import config.port as cp

from ..core.data_structures import SequenceType


def should_generate_sequence(
    intensity_category: str,
    rng: np.random.RandomState,
) -> bool:
    """Decide if a storm should be part of a multi-storm sequence.

    Higher intensity categories are more likely to produce sequences,
    reflecting that severe weather systems tend to produce multiple
    precipitation events.
    """
    prob = cp.SEQUENCE_PROBABILITY.get(intensity_category, 0.15)
    return rng.random() < prob


def sample_sequence_type(
    intensity_category: str,
    rng: np.random.RandomState,
) -> SequenceType:
    """Sample the type of multi-storm sequence.

    Returns doublet, cluster, or persistent based on intensity-dependent
    weights. More severe storms tend toward cluster/persistent patterns.
    """
    weights = cp.SEQUENCE_TYPE_WEIGHTS.get(intensity_category, cp.DEFAULT_TYPE_WEIGHTS)
    types = [SequenceType.DOUBLET, SequenceType.CLUSTER, SequenceType.PERSISTENT]
    idx = rng.choice(len(types), p=weights)
    return types[idx]


def get_storm_count(
    sequence_type: SequenceType,
    rng: np.random.RandomState,
) -> int:
    """Return number of storms for a sequence type (Table 1, SEQUENCE_STORM_COUNTS).

    A type with a single count takes it without drawing; otherwise the count is
    uniform over the range.
    """
    lo, hi = cp.SEQUENCE_STORM_COUNTS.get(sequence_type.value, (1, 1))
    return lo if lo == hi else rng.choice(list(range(lo, hi + 1)))


def sample_storm_intensity(
    base_intensity: float,
    storm_index: int,
    rng: np.random.RandomState,
) -> float:
    """Sample intensity for a storm within a sequence (Eqs. 12-13).

    Storm 0: a downward variation, Uniform(-v, 0). It is redrawn from the same law with
    probability 1 - FIRST_STORM_DOMINANT_PROB, which leaves its law unchanged.
    Later storms: Uniform(0, v) with probability CORRELATION_PROB, else Uniform(-v, 0).
    A later storm is then at least as strong as the first with probability
    CORRELATION_PROB + (1 - CORRELATION_PROB) / 2 (0.85 at the defaults).

    Returns:
        Adjusted intensity factor, floored at 0.1.
    """
    v = cp.INTENSITY_VARIATION
    if storm_index == 0:
        variation = rng.uniform(-v, 0.0)
        if rng.random() >= cp.FIRST_STORM_DOMINANT_PROB:
            variation = rng.uniform(-v, 0.0)
        return max(0.1, base_intensity * (1.0 + variation))

    if rng.random() < cp.CORRELATION_PROB:
        variation = rng.uniform(0.0, v)
    else:
        variation = rng.uniform(-v, 0.0)

    return max(0.1, base_intensity * (1.0 + variation))
