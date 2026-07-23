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

"""Population reweighting of the event catalogue (MKM-EF-001).

The storm catalogue is an *importance sample*, not a random sample of the
qualifying events a year contains. MKM-SS-001 generates it to train the stress
classifier, so it deliberately oversamples severe categories and omits the mild
ones entirely.

Resampling it uniformly and calling the answer P(flood | event) therefore
answers a different question — P(flood | event is at least moderate) — and
multiplying that by a λ that counts *all* qualifying events double-counts
severity. Left uncorrected it implied a severe flood every 0.81 years.

Each event is given the weight its intensity category carries in the real
population, divided by that category's share of the catalogue. Sampling
proportionally to those weights recovers the population the catalogue was drawn
from. This is the standard event-loss-table construction: a catalogue of events,
each with a rate.
"""

from typing import Any, Dict, Sequence

import numpy as np

from config.frequency import EVENT_POPULATION_WEIGHTS, INTENSITY_SEVERITY_ORDER

# Category assumed for a storm carrying no intensity label. The mildest
# category is the conservative choice for an unlabelled event: it keeps an
# unknown from being resampled as if it were a catastrophe.
DEFAULT_CATEGORY = INTENSITY_SEVERITY_ORDER[0]

_SEVERITY_RANK = {name: rank for rank, name in enumerate(INTENSITY_SEVERITY_ORDER)}


def storm_category(storm: Dict[str, Any]) -> str:
    """Return a storm's intensity category, defaulting when unlabelled.

    Args:
        storm: a storm dict from ``load_storms_from_sequences``.

    Returns:
        A category name from ``INTENSITY_SEVERITY_ORDER``. An unrecognised
        label is treated as unlabelled rather than raising, so one malformed
        storm cannot fail a whole catalogue build.
    """
    label = (storm.get("intensity_category") or "").strip().lower()
    return label if label in _SEVERITY_RANK else DEFAULT_CATEGORY


def event_category(categories: Sequence[str]) -> str:
    """Return the category of an event from its member storms' categories.

    An event takes the **most severe** category among its storms, matching the
    aggregation used for its level: the event is characterised by its worst
    moment, not its average one.

    Args:
        categories: the member storms' categories.

    Returns:
        The most severe category, or the default for an empty sequence.
    """
    if not categories:
        return DEFAULT_CATEGORY
    return max(categories, key=lambda name: _SEVERITY_RANK.get(name, 0))


def population_weights(categories: Sequence[str]) -> np.ndarray:
    """Return sampling weights that reweight a catalogue onto the population.

    For each event, the weight is its category's population frequency divided by
    that category's share of the catalogue. Events in an over-represented
    category are individually down-weighted, and vice versa.

    Args:
        categories: each event's intensity category, in catalogue order.

    Returns:
        Weights summing to one, aligned with *categories*. An empty catalogue
        returns an empty array. A catalogue whose categories all carry zero
        population weight falls back to uniform weights rather than dividing by
        zero — a degenerate catalogue is better sampled evenly than not at all.
    """
    if not categories:
        return np.zeros(0, dtype=float)

    counts: Dict[str, int] = {}
    for category in categories:
        counts[category] = counts.get(category, 0) + 1

    weights = np.array(
        [EVENT_POPULATION_WEIGHTS.get(c, 0.0) / counts[c] for c in categories],
        dtype=float,
    )

    total = weights.sum()
    if total <= 0:
        return np.full(len(categories), 1.0 / len(categories), dtype=float)
    return weights / total


def effective_sample_size(weights: np.ndarray) -> float:
    """Return Kish's effective sample size for a weight vector.

    Reweighting costs precision: if a handful of events carry most of the
    weight, the catalogue behaves like a much smaller one and the simulation is
    noisier than its event count suggests. This is the diagnostic that says how
    much smaller.

    Args:
        weights: normalised sampling weights.

    Returns:
        ``1 / sum(w^2)``, which equals the event count for uniform weights and
        falls towards one as the weight concentrates. Zero for an empty vector.
    """
    if weights.size == 0:
        return 0.0
    return float(1.0 / np.sum(np.square(weights)))
