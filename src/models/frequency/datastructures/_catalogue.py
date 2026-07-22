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

"""The event catalogue for the Event Frequency Model (MKM-EF-001).

One row per *event* — a storm sequence inside the insurance hours clause — and
one column per gauge, holding the highest level that event drove at that gauge.

This is the structure the year sampler resamples from. Because every gauge's
outcome for a given event sits in the same row, drawing an event row draws a
spatially coherent storm: the correlation between gauges is carried by the
catalogue itself rather than having to be modelled again downstream.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass(frozen=True)
class EventCatalogue:
    """Per-event peak levels at every gauge.

    Attributes:
        event_ids: the events, in first-appearance order.
        storms_per_event: how many storms each event was built from. Retained
            because the ratio of storms to events is the quantity that changes
            when pricing moves off a per-storm denominator, and it has to be
            reportable rather than inferred.
        peak_levels: gauge identifier to that gauge's peak level for each event,
            aligned with ``event_ids``.
    """

    event_ids: Tuple[str, ...]
    storms_per_event: Tuple[int, ...]
    peak_levels: Dict[str, np.ndarray]

    @property
    def n_events(self) -> int:
        """Return the number of events in the catalogue."""
        return len(self.event_ids)

    @property
    def n_storms(self) -> int:
        """Return the number of storms the events were built from."""
        return int(sum(self.storms_per_event))

    @property
    def gauge_ids(self) -> Tuple[str, ...]:
        """Return the gauges the catalogue covers, in insertion order."""
        return tuple(self.peak_levels.keys())

    def flood_flags(self, gauge_id: str, threshold_m: float) -> np.ndarray:
        """Return, per event, whether that event took *gauge_id* over a level.

        This is the vector the year sampler scores against. An unknown gauge
        yields all-False rather than raising, so a portfolio run is not derailed
        by one gauge missing from the catalogue.

        Args:
            gauge_id: the gauge to test.
            threshold_m: the level defining a flood, in metres.

        Returns:
            A boolean array of length ``n_events``.
        """
        levels = self.peak_levels.get(gauge_id)
        if levels is None:
            return np.zeros(self.n_events, dtype=bool)
        return levels >= threshold_m

    def conditional_probability(self, gauge_id: str, threshold_m: float) -> float:
        """Return P(flood at *gauge_id* | event) implied by the catalogue.

        The conditional half of the decomposition: multiplied by the catchment
        arrival rate it gives the annual rate.

        Args:
            gauge_id: the gauge to test.
            threshold_m: the level defining a flood, in metres.

        Returns:
            A probability in ``[0, 1]``; zero for an empty catalogue.
        """
        if self.n_events == 0:
            return 0.0
        return float(self.flood_flags(gauge_id, threshold_m).mean())
