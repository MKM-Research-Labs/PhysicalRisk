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

"""Loss-weighted year sampling for the Event Frequency Model (MKM-EF-001).

Stage 6. The occurrence sampler in ``_sample.py`` scores each drawn event with a
boolean flood flag; this scores it with a loss quantum instead. Everything else
is shared: the *same* ``EventDraws`` produced by ``draw_event_years`` feeds both,
so a subject's occurrence run and its loss run describe the same simulated
storms, and a portfolio's subjects stay correlated through the events they share.
Draw once, apply many — here ``apply_catalogue_losses`` is the per-subject step.

The loss quantum per catalogue event is the caller's: the pricing leg turns a
peak level into a monetary loss through its own damage model, and hands the
result in as ``event_losses``. The frequency layer supplies only the machinery
that turns per-event losses into an annual distribution, exactly as §4.14 of the
plan anticipated.
"""

from typing import Optional

import numpy as np

from config.frequency import SimulationConfig

from ..datastructures import EventDraws, LossSimulation
from ._sample import draw_event_years


def _empty(draws: EventDraws) -> LossSimulation:
    """Return a zero-loss simulation for an empty catalogue or run."""
    return LossSimulation(
        n_years=draws.n_years,
        lambda_per_year=draws.lambda_per_year,
        aggregate_loss_per_year=np.zeros(draws.n_years, dtype=float),
        max_event_loss_per_year=np.zeros(draws.n_years, dtype=float),
        seed=draws.seed,
    )


def apply_catalogue_losses(
    draws: EventDraws,
    event_losses: np.ndarray,
) -> LossSimulation:
    """Score one subject's per-event losses against a set of year draws.

    Args:
        draws: the shared per-run event draws.
        event_losses: one non-negative loss per catalogue event — the loss that
            event causes this subject. Negative entries would break the
            zero-loss-for-an-empty-year convention and are not expected; losses
            are damage quanta.

    Returns:
        A ``LossSimulation``. An empty catalogue or run yields zero losses
        rather than raising, so a subject with no computed losses does not
        derail a portfolio run.
    """
    losses = np.asarray(event_losses, dtype=float)
    if (losses.size == 0 or draws.n_years == 0
            or draws.event_indices.size == 0):
        return _empty(draws)

    # The loss of every drawn event, flat and in year order — the loss analogue
    # of the flooded-flag lookup in apply_catalogue.
    drawn = losses[draws.event_indices]

    # Aggregate per year by differencing the cumulative sum at the year
    # boundaries. Looping per year is the obvious shape and two orders of
    # magnitude slower at these year counts.
    boundaries = np.concatenate(([0], np.cumsum(draws.events_per_year)))
    cumulative = np.concatenate(([0.0], np.cumsum(drawn)))
    aggregate = cumulative[boundaries[1:]] - cumulative[boundaries[:-1]]

    # Largest single occurrence per year. maximum.at scatters each drawn loss
    # into its year and keeps the running maximum; a year with no events keeps
    # the initialised zero, which is correct because losses are non-negative.
    year_of = np.repeat(np.arange(draws.n_years), draws.events_per_year)
    max_event = np.zeros(draws.n_years, dtype=float)
    np.maximum.at(max_event, year_of, drawn)

    return LossSimulation(
        n_years=draws.n_years,
        lambda_per_year=draws.lambda_per_year,
        aggregate_loss_per_year=aggregate,
        max_event_loss_per_year=max_event,
        seed=draws.seed,
    )


def simulate_losses(
    event_losses: np.ndarray,
    lambda_per_year: float,
    config: SimulationConfig,
    seed: Optional[int] = None,
    n_years: Optional[int] = None,
    weights: Optional[np.ndarray] = None,
) -> LossSimulation:
    """Run a single-subject loss simulation.

    A convenience wrapper over ``draw_event_years`` and
    ``apply_catalogue_losses``. Portfolio callers must not use it per subject —
    that would draw independent storms for each and destroy their correlation.
    Draw once, apply many.

    Args:
        event_losses: one non-negative loss per catalogue event for the subject.
        lambda_per_year: the catchment arrival rate.
        config: simulation knobs.
        seed: seed override; defaults to the configured seed.
        n_years: year-count override; defaults to the configured count.
        weights: per-event sampling weights; see ``draw_event_years``. Pass the
            catalogue's weights so the drawn events match the population the
            losses were computed over.

    Returns:
        A ``LossSimulation``.
    """
    losses = np.asarray(event_losses, dtype=float)
    draws = draw_event_years(
        losses.size, lambda_per_year, config, seed, n_years, weights)
    return apply_catalogue_losses(draws, losses)
