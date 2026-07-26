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

"""Turning a subject's per-event outcomes into a loss table (MKM-EF-001, 6b).

Stage 6a built the loss machinery and left the loss quantum to the caller. This
is the adapter the pricing legs call: it turns what a subject already has — a
gauge's per-event peak levels, or an asset's per-storm flood records — into a
per-event loss vector aligned with the catalogue, then assembles the event loss
table and the annual loss distribution.

The damage model stays with the caller. A gauge subject passes a ``loss_fn``
that maps a peak level to a loss; an asset leg passes the per-record losses it
computed from its own depth-damage curve and property value. The frequency
layer never imports a damage model — it only does the alignment arithmetic and
the assembly, which is what keeps it generic across perils.

One trap this module exists to close. The event loss table takes the *raw*
catchment rate and scales it by the catalogue coverage internally; the year
sampler takes the rate it should draw at directly and does *not*. Feeding the
sampler the raw rate would silently overstate every loss by ``1/coverage``.
``shared_draws`` and ``loss_metrics`` apply the coverage scaling in one place so
no call site can get the two out of step.
"""

from typing import Callable, Dict, Iterable, Optional, Sequence, Tuple, Union

import numpy as np

from config.frequency import SimulationConfig

from .datastructures import EventCatalogue, EventDraws, EventFrame
from .elt import build_event_loss_table, elt_document
from .ylt import (
    apply_catalogue_losses,
    draw_event_years,
    reconcile_losses,
    simulate_losses,
)

# Either structure carries the event identities, weights and coverage the loss
# assembly needs; the catalogue additionally carries per-gauge peak levels.
Events = Union[EventCatalogue, EventFrame]


def peak_level_losses(
    catalogue: EventCatalogue,
    gauge_id: str,
    loss_fn: Callable[[float], float],
) -> np.ndarray:
    """Return a gauge's per-event loss vector, aligned with the catalogue.

    Each event's loss is ``loss_fn`` applied to that event's peak level at the
    gauge. The catalogue's ``peak_levels`` are already aligned with
    ``event_ids``, so a gauge subject needs no regrouping.

    Args:
        catalogue: the event catalogue.
        gauge_id: the gauge to price.
        loss_fn: maps a peak level in metres to a loss. The caller composes the
            damage curve and any exposure value into it; the result is clamped
            at zero so a curve that dips negative cannot manufacture a gain.

    Returns:
        A float array of length ``catalogue.n_events``. An unknown gauge yields
        all-zero losses rather than raising, mirroring ``flood_flags``, so one
        missing gauge does not derail a portfolio run.
    """
    levels = catalogue.peak_levels.get(gauge_id)
    if levels is None:
        return np.zeros(catalogue.n_events, dtype=float)
    return np.array([max(0.0, float(loss_fn(float(level)))) for level in levels])


def regrouped_event_losses(
    frame: Events,
    identifiers: Iterable[str],
    losses: Sequence[float],
) -> np.ndarray:
    """Regroup an asset's per-record losses onto events, aligned with the frame.

    The property and commercial legs hold per-storm flood records, not gauge
    levels. This collapses those records onto events, taking the *maximum* loss
    within each event. The maximum matches the occurrence rule the rest of the
    chain uses: a week containing two breaches is one loss occurrence, valued at
    its worst moment.

    Args:
        frame: the event structure the losses will be scored against.
        identifiers: the storm or event identifier each record belongs to, in
            the same order as ``losses``.
        losses: the loss of each record to the subject.

    Returns:
        A float array of length ``frame.n_events``.

    Raises:
        ValueError: if the two inputs differ in length, or if any identifier
            matches neither a storm nor an event in the frame — the same
            strictness as ``EventFrame.conditional_probability``, because a
            record that does not correspond to this storm set would otherwise
            contribute a plausible but meaningless loss.
    """
    identifiers = list(identifiers)
    loss_values = np.asarray(losses, dtype=float)
    if len(identifiers) != loss_values.size:
        raise ValueError(
            f"{len(identifiers)} identifiers but {loss_values.size} losses; "
            "they must correspond one to one")

    index_of = {event_id: position
                for position, event_id in enumerate(frame.event_ids)}
    event_of = getattr(frame, "event_of", {})
    out = np.zeros(frame.n_events, dtype=float)

    unresolved = 0
    for identifier, loss in zip(identifiers, loss_values):
        if identifier in index_of:
            position = index_of[identifier]
        elif identifier in event_of:
            position = index_of[event_of[identifier]]
        else:
            unresolved += 1
            continue
        if loss > out[position]:
            out[position] = loss

    if unresolved:
        raise ValueError(
            f"{unresolved} of {len(identifiers)} identifiers match no storm or "
            "event in this frame; the records and the catalogue describe "
            "different storm sets")
    return out


def shared_draws(
    events: Events,
    lambda_per_year: float,
    config: SimulationConfig,
    seed: Optional[int] = None,
    n_years: Optional[int] = None,
) -> EventDraws:
    """Draw the events for a run once, at the coverage-scaled rate.

    Portfolio subjects must share one set of draws to stay correlated through
    the storms they share. This draws at ``lambda_per_year * coverage`` — the
    rate of catalogue-representable events, the rate the sampler must see — so
    that a caller cannot pass the raw rate to the sampler by mistake.

    Args:
        events: the catalogue or frame being sampled.
        lambda_per_year: the raw catchment arrival rate over all qualifying
            events.
        config: simulation knobs supplying the year-count and seed defaults.
        seed: seed override; defaults to the configured seed.
        n_years: year-count override; defaults to the configured count.

    Returns:
        An ``EventDraws`` to pass to ``loss_metrics`` for every subject in the
        run.
    """
    lambda_effective = max(0.0, lambda_per_year) * events.coverage
    return draw_event_years(
        events.n_events, lambda_effective, config, seed, n_years, events.weights)


def loss_metrics(
    events: Events,
    event_losses: np.ndarray,
    lambda_per_year: float,
    config: SimulationConfig,
    subject_id: str,
    catchment: str,
    provenance_class: str,
    return_periods: Tuple[int, ...],
    config_hash: Optional[str] = None,
    draws: Optional[EventDraws] = None,
) -> Dict:
    """Assemble one subject's loss table and annual loss distribution.

    The single place the coverage scaling is applied: the event loss table takes
    the raw ``lambda_per_year`` and scales it itself, while the sampler is driven
    at the effective rate, so the table's closed-form average annual loss and the
    simulation's mean agree by construction and are reconciled here.

    Args:
        events: the catalogue (gauge subjects) or frame (asset subjects).
        event_losses: the subject's per-event losses, aligned with
            ``events.event_ids``.
        lambda_per_year: the raw catchment arrival rate.
        config: simulation knobs.
        subject_id: the gauge, property or asset the losses are for.
        catchment: the catchment, recorded in the export metadata.
        provenance_class: how the underlying rate was obtained, as its string;
            carried into the export so a generator-derived table cannot read as
            observed.
        return_periods: the return-period grid for the AEP and OEP curves.
        config_hash: the frequency-config hash, recorded in the export.
        draws: shared run draws from ``shared_draws``; when given, every subject
            is scored against the same storms. When omitted, the subject is
            sampled on its own, which is correct only for a single-subject run.

    Returns:
        A JSON-serialisable dict: the attributed event loss table, the average
        annual loss, the AEP and OEP curves, and the reconciliation verdict.
    """
    losses = np.asarray(event_losses, dtype=float)
    table = build_event_loss_table(events, losses, lambda_per_year, subject_id)
    lambda_effective = table.lambda_effective

    if draws is None:
        simulation = simulate_losses(
            losses, lambda_effective, config, weights=events.weights)
    else:
        simulation = apply_catalogue_losses(draws, losses)

    within, sigmas = reconcile_losses(
        simulation, lambda_effective, events.weights, losses, config)

    return {
        "elt": elt_document(table, catchment, provenance_class, config_hash),
        "average_annual_loss": simulation.average_annual_loss(),
        "aep": simulation.aep_curve(return_periods),
        "oep": simulation.oep_curve(return_periods),
        "reconciliation": {
            "within_tolerance": within,
            "deviation_sigmas": sigmas,
        },
    }
