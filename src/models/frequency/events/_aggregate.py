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

"""Aggregating per-storm gauge responses into events (MKM-EF-001).

The hazard model routes each storm through the gauge response model
individually, and that physics is left alone. What changes here is only the
*grouping*: the one to five storms of a sequence sit inside a single 168-hour
hours-clause event, and an event is what arrives at a rate.

An event's level at a gauge is the highest level any of its member storms
drove there. The maximum is the right aggregator for an occurrence trigger: a
PRS pays on the level being breached, and a week containing two separate
breaches is one breach of the contract, not two. It also matches how the hours
clause is used in reinsurance, where everything inside the window is one loss
occurrence.

Note that this reduces the flood count even before any arrival rate is applied.
That effect is the denominator change, and it is deliberately separated from
the rate change so the two can be measured apart.
"""

from typing import Any, Dict, List, Sequence

import numpy as np

from models.hazard.io import event_id

from ..datastructures import EventCatalogue
from ._weights import event_category, population_weights, storm_category


def storm_to_event(storms: Sequence[Dict[str, Any]]) -> Dict[str, str]:
    """Map each storm identifier to the event it belongs to.

    The tag-reading rule itself lives with the loader that writes the tag, so
    the two cannot drift; this only builds the lookup.

    Args:
        storms: storm dicts as produced by ``load_storms_from_sequences``.

    Returns:
        Storm identifier to event identifier.
    """
    return {storm["storm_id"]: event_id(storm) for storm in storms}


def event_order(storms: Sequence[Dict[str, Any]]) -> List[str]:
    """Return the distinct event identifiers in first-appearance order.

    Args:
        storms: storm dicts as produced by ``load_storms_from_sequences``.

    Returns:
        Event identifiers, de-duplicated, order preserved so a catalogue built
        twice from the same input is byte-identical.
    """
    mapping = storm_to_event(storms)
    seen: Dict[str, None] = {}
    for storm in storms:
        seen.setdefault(mapping[storm["storm_id"]], None)
    return list(seen)


def build_catalogue(
    responses: Dict[str, List[Any]],
    storms: Sequence[Dict[str, Any]],
) -> EventCatalogue:
    """Group per-storm gauge responses into a per-event catalogue.

    Args:
        responses: gauge identifier to that gauge's ``GaugeResponse`` list, as
            returned by ``HazardCurveBuilder.build``. Each response carries the
            ``storm_id`` it belongs to, so grouping is by identity rather than
            by position — the two coincide today, but position would break
            silently if response ordering ever changed.
        storms: the storm dicts the responses were computed from.

    Returns:
        An ``EventCatalogue``. Events with no response at a given gauge take
        that gauge's lowest observed level rather than zero, so a missing
        response cannot read as a dry event at a gauge whose datum is negative.
    """
    events = event_order(storms)
    index_of = {event_id: position for position, event_id in enumerate(events)}
    mapping = storm_to_event(storms)

    storms_per_event = [0] * len(events)
    member_categories = [[] for _ in events]
    for storm in storms:
        position = index_of[mapping[storm["storm_id"]]]
        storms_per_event[position] += 1
        member_categories[position].append(storm_category(storm))

    # An event's category is its most severe storm's, matching how its level is
    # aggregated: the event is characterised by its worst moment.
    categories = [event_category(members) for members in member_categories]

    peak_levels: Dict[str, np.ndarray] = {}
    for gauge_id, gauge_responses in responses.items():
        if not gauge_responses:
            peak_levels[gauge_id] = np.zeros(len(events), dtype=float)
            continue

        floor = min(response.peak_level_m for response in gauge_responses)
        levels = np.full(len(events), floor, dtype=float)
        for response in gauge_responses:
            event_id = mapping.get(response.storm_id)
            if event_id is None:
                # A response whose storm is not in the supplied catalogue is
                # skipped rather than guessed at.
                continue
            position = index_of[event_id]
            if response.peak_level_m > levels[position]:
                levels[position] = response.peak_level_m
        peak_levels[gauge_id] = levels

    return EventCatalogue(
        event_ids=tuple(events),
        storms_per_event=tuple(storms_per_event),
        categories=tuple(categories),
        weights=population_weights(categories),
        peak_levels=peak_levels,
    )
