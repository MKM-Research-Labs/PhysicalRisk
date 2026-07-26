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

"""Building an event loss table from a catalogue (MKM-EF-001, Stage 6).

The catalogue already carries everything an ELT needs bar the losses: the event
identifiers, the per-event sampling weights, and the coverage that scales the
catchment rate down to the events the catalogue can represent. Attach the
subject's per-event losses and the table is complete.

Each event's annual rate is ``lambda_effective * weight``, where
``lambda_effective = lambda_per_year * coverage``. The weights sum to one, so
the rates sum to ``lambda_effective`` — the arrival rate of
catalogue-representable events, the same rate the loss sampler draws at. This
alignment is deliberate: it is what makes the table's closed-form average annual
loss the exact expectation of the sampler's mean aggregate loss.
"""

import numpy as np

from ..datastructures import EventCatalogue, EventLossTable


def build_event_loss_table(
    catalogue: EventCatalogue,
    event_losses: np.ndarray,
    lambda_per_year: float,
    subject_id: str,
) -> EventLossTable:
    """Assemble the event loss table for one subject.

    Args:
        catalogue: the event catalogue the losses were computed against; it
            supplies the event identifiers, the sampling weights and the
            coverage.
        event_losses: one loss per catalogue event, aligned with
            ``catalogue.event_ids``.
        lambda_per_year: the catchment arrival rate over all qualifying events;
            scaled by the catalogue coverage to the rate of representable events.
        subject_id: the gauge, property or portfolio the losses are for.

    Returns:
        An ``EventLossTable`` whose rates sum to
        ``lambda_per_year * coverage``.

    Raises:
        ValueError: if the loss vector does not align with the catalogue, which
            would silently misattribute losses to events.
    """
    losses = np.asarray(event_losses, dtype=float)
    if losses.size != catalogue.n_events:
        raise ValueError(
            f"event_losses has {losses.size} entries but the catalogue has "
            f"{catalogue.n_events} events; they must align one to one")

    lambda_effective = max(0.0, lambda_per_year) * catalogue.coverage
    rates = lambda_effective * np.asarray(catalogue.weights, dtype=float)

    return EventLossTable(
        subject_id=subject_id,
        event_ids=catalogue.event_ids,
        rates=rates,
        losses=losses,
        lambda_effective=lambda_effective,
    )
