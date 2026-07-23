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

"""Year-loss-table sampling for the Event Frequency Model (MKM-EF-001).

Draws the number of qualifying storm events in a simulated year and resamples
that many events from the pre-computed catalogue, recording how many of them
flood. Repeating gives the annual flood distribution.

The draw is deliberately separated from its application. A storm arrives over
the *catchment* and reaches every gauge and property in it, so one set of draws
must serve every subject in a portfolio run: ``draw_event_years`` once, then
``apply_catalogue`` per subject. Drawing independently per subject would
discard the spatial correlation the existing per-event model already supplies,
and portfolio risk would collapse towards zero — a portfolio of two hundred
gauges would look two hundred times better diversified than it is.

Resampling rather than regenerating is what makes the accuracy affordable. The
catalogue's flood outcomes are already computed, so a simulated year is index
lookups; a hundred thousand years costs about what a thousand would have cost
under a regeneration design.
"""

from typing import Optional

import numpy as np

from config.frequency import SimulationConfig

from ..datastructures import EventDraws, YearSimulation


def _conditional(flags: np.ndarray, weights: Optional[np.ndarray]) -> float:
    """Return P(flood | event) for a subject under the sampling weights.

    Args:
        flags: per-event flood outcomes.
        weights: per-event sampling weights, or None for a uniform catalogue.

    Returns:
        The weighted fraction of events that flood, or zero for an empty
        catalogue.
    """
    if flags.size == 0:
        return 0.0
    if weights is None or weights.size != flags.size:
        return float(flags.mean())
    return float(np.dot(flags, weights))


def simulate_annual_counts(
    lambda_per_year: float,
    n_years: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Draw the number of qualifying events arriving in each simulated year.

    Args:
        lambda_per_year: the catchment arrival rate. Negative rates are treated
            as zero.
        n_years: number of years to simulate.
        rng: caller-owned generator, so runs are reproducible.

    Returns:
        An integer array of length *n_years*.
    """
    return rng.poisson(max(0.0, lambda_per_year), size=n_years)


def draw_event_years(
    n_catalogue_events: int,
    lambda_per_year: float,
    config: SimulationConfig,
    seed: Optional[int] = None,
    n_years: Optional[int] = None,
    weights: Optional[np.ndarray] = None,
) -> EventDraws:
    """Draw the events arriving in each simulated year, once for a whole run.

    The result is shared across every subject in the run, which is what keeps
    gauges and properties correlated through the storms they actually share.

    Args:
        n_catalogue_events: size of the event catalogue being resampled.
        lambda_per_year: the catchment arrival rate.
        config: simulation knobs supplying the year-count and seed defaults.
        seed: seed override; defaults to the configured seed.
        n_years: year-count override; defaults to the configured count.
        weights: per-event sampling weights summing to one, from the
            catalogue. Omitting them samples uniformly, which is only correct
            for a catalogue that is already a fair sample of the event
            population — the generated storm catalogue is not, so callers
            should pass ``catalogue.weights``.

    Returns:
        An ``EventDraws`` carrying the per-year counts and the flat array of
        drawn catalogue indices. An empty catalogue yields no draws.
    """
    years = config.n_years if n_years is None else n_years
    used_seed = config.seed if seed is None else seed
    rng = np.random.default_rng(used_seed)

    counts = simulate_annual_counts(lambda_per_year, years, rng)
    if n_catalogue_events <= 0:
        counts = np.zeros(years, dtype=np.int64)
        indices = np.zeros(0, dtype=np.int64)
    elif weights is None or weights.size != n_catalogue_events:
        indices = rng.integers(0, n_catalogue_events, size=int(counts.sum()))
    else:
        # Inverse-transform sampling against the cumulative weights. Much faster
        # than rng.choice(p=...) at these draw counts, which rebuilds the
        # distribution on every call.
        cumulative = np.cumsum(weights)
        cumulative[-1] = 1.0
        indices = np.searchsorted(
            cumulative, rng.random(int(counts.sum())), side="right")
        np.clip(indices, 0, n_catalogue_events - 1, out=indices)

    return EventDraws(
        n_years=years,
        lambda_per_year=lambda_per_year,
        events_per_year=counts,
        event_indices=indices,
        seed=used_seed,
    )


def apply_catalogue(
    draws: EventDraws,
    event_floods: np.ndarray,
    weights: Optional[np.ndarray] = None,
) -> YearSimulation:
    """Score one subject's catalogue outcomes against a set of year draws.

    Args:
        draws: the shared per-run event draws.
        event_floods: boolean array, one entry per catalogue event, True where
            that event floods this subject.
        weights: the same per-event weights the draws used. Needed so the
            reported conditional matches the population the draws came from;
            omitting them reports the unweighted catalogue mean.

    Returns:
        A ``YearSimulation``. An empty catalogue yields a run with no floods
        rather than raising, so a subject with no computed responses does not
        derail a portfolio run.
    """
    flags = np.asarray(event_floods, dtype=bool)

    if flags.size == 0 or draws.n_years == 0 or draws.event_indices.size == 0:
        return YearSimulation(
            n_years=draws.n_years,
            lambda_per_year=draws.lambda_per_year,
            p_event=_conditional(flags, weights),
            events_per_year=draws.events_per_year,
            flood_events_per_year=np.zeros(draws.n_years, dtype=np.int64),
            seed=draws.seed,
        )

    # Score every drawn event in one flat pass, then split the flat result back
    # into years with a cumulative sum. Looping per year is the obvious shape
    # and is roughly two orders of magnitude slower at these year counts.
    flooded = flags[draws.event_indices]
    boundaries = np.concatenate(([0], np.cumsum(draws.events_per_year)))
    cumulative = np.concatenate(([0], np.cumsum(flooded)))
    floods = (cumulative[boundaries[1:]] - cumulative[boundaries[:-1]]).astype(np.int64)

    return YearSimulation(
        n_years=draws.n_years,
        lambda_per_year=draws.lambda_per_year,
        p_event=_conditional(flags, weights),
        events_per_year=draws.events_per_year,
        flood_events_per_year=floods,
        seed=draws.seed,
    )


def simulate_years(
    event_floods: np.ndarray,
    lambda_per_year: float,
    config: SimulationConfig,
    seed: Optional[int] = None,
    n_years: Optional[int] = None,
    weights: Optional[np.ndarray] = None,
) -> YearSimulation:
    """Run a single-subject year simulation.

    A convenience wrapper over ``draw_event_years`` and ``apply_catalogue``.
    Portfolio callers must not use it per subject — that would draw independent
    storms for each and destroy their correlation. Draw once, apply many.

    Args:
        event_floods: boolean array of per-event flood outcomes for the subject.
        lambda_per_year: the catchment arrival rate.
        config: simulation knobs.
        seed: seed override; defaults to the configured seed.
        n_years: year-count override; defaults to the configured count.
        weights: per-event sampling weights; see ``draw_event_years``.

    Returns:
        A ``YearSimulation``.
    """
    flags = np.asarray(event_floods, dtype=bool)
    draws = draw_event_years(
        flags.size, lambda_per_year, config, seed, n_years, weights)
    return apply_catalogue(draws, flags, weights)
