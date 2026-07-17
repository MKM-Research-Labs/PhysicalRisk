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
Intensity sampler for Storm Generator v2.0 multi-storm sequences.

Controls whether a storm becomes part of a sequence, what type of
sequence, how many storms, and the correlated intensity relationship
between successive storms in a sequence.
"""

from typing import List, Tuple

import numpy as np

from config.port import (
    CORRELATION_PROB,
    DEFAULT_TYPE_WEIGHTS,
    FIRST_STORM_DOMINANT_PROB,
    INTENSITY_VARIATION,
    SEQUENCE_PROBABILITY,
)
from ..core.data_structures import SequenceType

# SEQUENCE_PROBABILITY, DEFAULT_TYPE_WEIGHTS, INTENSITY_VARIATION,
# FIRST_STORM_DOMINANT_PROB, CORRELATION_PROB imported from config/port.py

# Weights for [doublet, cluster, persistent] by intensity
SEQUENCE_TYPE_WEIGHTS = {
    "moderate": [0.50, 0.35, 0.15],
    "severe": [0.30, 0.50, 0.20],
    "extreme": [0.20, 0.45, 0.35],
    "catastrophic": [0.15, 0.45, 0.40],
}


def should_generate_sequence(
    intensity_category: str,
    rng: np.random.RandomState,
) -> bool:
    """Decide if a storm should be part of a multi-storm sequence.

    Higher intensity categories are more likely to produce sequences,
    reflecting that severe weather systems tend to produce multiple
    precipitation events.
    """
    prob = SEQUENCE_PROBABILITY.get(intensity_category, 0.15)
    return rng.random() < prob


def sample_sequence_type(
    intensity_category: str,
    rng: np.random.RandomState,
) -> SequenceType:
    """Sample the type of multi-storm sequence.

    Returns doublet, cluster, or persistent based on intensity-dependent
    weights. More severe storms tend toward cluster/persistent patterns.
    """
    weights = SEQUENCE_TYPE_WEIGHTS.get(intensity_category, DEFAULT_TYPE_WEIGHTS)
    types = [SequenceType.DOUBLET, SequenceType.CLUSTER, SequenceType.PERSISTENT]
    idx = rng.choice(len(types), p=weights)
    return types[idx]


def get_storm_count(
    sequence_type: SequenceType,
    rng: np.random.RandomState,
) -> int:
    """Return number of storms for a sequence type.

    isolated=1, doublet=2, cluster=3-4, persistent=4-5.
    """
    if sequence_type == SequenceType.ISOLATED:
        return 1
    if sequence_type == SequenceType.DOUBLET:
        return 2
    if sequence_type == SequenceType.CLUSTER:
        return rng.choice([3, 4])
    if sequence_type == SequenceType.PERSISTENT:
        return rng.choice([4, 5])
    return 1


def sample_storm_intensity(
    base_intensity: float,
    storm_index: int,
    rng: np.random.RandomState,
) -> float:
    """Sample intensity for a storm within a sequence.

    For storm 0 (or with FIRST_STORM_DOMINANT_PROB): intensity may be
    slightly reduced (up to -20%).
    For subsequent storms (70% of the time): intensity is maintained or
    increased (up to +20%), modeling compounding from antecedent wetness.

    Args:
        base_intensity: Base intensity factor for the sequence.
        storm_index: 0-based index of the storm in the sequence.
        rng: Random state.

    Returns:
        Adjusted intensity factor (always positive).
    """
    if storm_index == 0:
        # First storm: slight downward variation possible
        variation = rng.uniform(-INTENSITY_VARIATION, 0.0)
        if rng.random() >= FIRST_STORM_DOMINANT_PROB:
            variation = rng.uniform(-INTENSITY_VARIATION, 0.0)
        return max(0.1, base_intensity * (1.0 + variation))

    # Subsequent storms: 70% chance of maintaining/increasing
    if rng.random() < CORRELATION_PROB:
        variation = rng.uniform(0.0, INTENSITY_VARIATION)
    else:
        variation = rng.uniform(-INTENSITY_VARIATION, 0.0)

    return max(0.1, base_intensity * (1.0 + variation))
