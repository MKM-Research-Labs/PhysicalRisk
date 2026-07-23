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

"""The event frame for the Event Frequency Model (MKM-EF-001).

Which storms belong to which hours-clause event, and what each event weighs in
the population. This is everything needed to turn a *subject's* per-storm
outcomes into a per-event conditional, and it is derivable from the storm
sequences alone.

Separated from ``EventCatalogue`` because the property and commercial legs
price off their own per-asset flood records rather than off gauge levels, and
so need the grouping without needing anyone's peak levels.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np


@dataclass(frozen=True)
class EventFrame:
    """The hours-clause event structure of a storm catalogue.

    Attributes:
        event_ids: the events, in first-appearance order.
        storms_per_event: how many storms each event was built from.
        categories: each event's intensity category.
        weights: per-event sampling weight, summing to one.
        coverage: the share of the whole event population these events
            represent. Mild categories absent from the generated catalogue are
            real events that never reach a trigger, so the conditional is
            scaled by this rather than the weights being renormalised.
        event_of: storm identifier to the event it belongs to.
    """

    event_ids: Tuple[str, ...]
    storms_per_event: Tuple[int, ...]
    categories: Tuple[str, ...]
    weights: np.ndarray
    coverage: float
    event_of: Dict[str, str]

    @property
    def n_events(self) -> int:
        """Return the number of events."""
        return len(self.event_ids)

    @property
    def n_storms(self) -> int:
        """Return the number of storms the events were built from."""
        return int(sum(self.storms_per_event))

    def resolve(self, identifiers: Iterable[str]) -> Tuple[set, int]:
        """Resolve storm or event identifiers to the events they belong to.

        Callers hand over whatever their own records carry, and those records
        are not consistent: the property flood series names its field
        ``storm_id`` but stores *sequence* identifiers, because the generator
        collapses storms onto sequences before writing and the loop variable
        kept the old name. Accepting both, and counting what matches neither,
        is safer than trusting the field name.

        Args:
            identifiers: storm or event identifiers.

        Returns:
            ``(events_hit, n_unresolved)``. A non-zero second element means the
            caller's records and this frame describe different storm sets, and
            any conditional computed from them would be meaningless.
        """
        known = set(self.event_ids)
        hit, unresolved = set(), 0
        for identifier in identifiers:
            if identifier in known:
                hit.add(identifier)
            elif identifier in self.event_of:
                hit.add(self.event_of[identifier])
            else:
                unresolved += 1
        return hit, unresolved

    def event_flags(self, identifiers: Iterable[str]) -> np.ndarray:
        """Return, per event, whether any of *identifiers* falls inside it.

        The union is the right rule for an occurrence trigger: an event counts
        once however many of its member storms flooded the subject, because a
        week containing two breaches is one breach of the contract.

        Args:
            identifiers: storm or event identifiers in which the subject flooded.

        Returns:
            A boolean array of length ``n_events``.
        """
        hit, _ = self.resolve(identifiers)
        return np.fromiter(
            (event_id in hit for event_id in self.event_ids),
            dtype=bool,
            count=self.n_events,
        )

    def conditional_probability(self, identifiers: Iterable[str]) -> float:
        """Return P(subject floods | event) over the whole event population.

        Args:
            identifiers: storm or event identifiers in which the subject flooded.

        Returns:
            A probability in ``[0, 1]``; zero for an empty frame.

        Raises:
            ValueError: if any identifier matches neither a storm nor an event
                in this frame. Silently dropping them would return a plausible
                small number from records that do not correspond to this storm
                set at all — the failure mode that produced a confident 0.0
                from 110 genuine flood events during development.
        """
        if self.n_events == 0:
            return 0.0
        identifiers = list(identifiers)
        hit, unresolved = self.resolve(identifiers)
        if unresolved:
            raise ValueError(
                f"{unresolved} of {len(identifiers)} identifiers match no storm "
                "or event in this frame; the records and the storm catalogue "
                "describe different storm sets"
            )
        flags = np.fromiter(
            (event_id in hit for event_id in self.event_ids),
            dtype=bool, count=self.n_events)
        return float(np.dot(flags, self.weights)) * self.coverage
