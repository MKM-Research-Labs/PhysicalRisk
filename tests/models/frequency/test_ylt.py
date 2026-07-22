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

"""Tests for the Monte Carlo year simulation (MKM-EF-001).

The simulation draws how many qualifying storm events arrive in a year, asks of
each whether it floods, and records whether the year flooded. These tests fix
the three properties that make it usable for pricing:

- it agrees with its closed form, which is its exact expectation;
- one set of draws serves a whole portfolio, so subjects stay correlated
  through the storms they share;
- a run is reproducible from its seed.
"""

import numpy as np
import pytest

from config.frequency import SimulationConfig, load_frequency_config
from models.frequency.datastructures import EventDraws, YearSimulation
from models.frequency.ylt import (
    analytic_annual_probability,
    analytic_expected_floods,
    apply_catalogue,
    draw_event_years,
    reconcile,
    simulate_annual_counts,
    simulate_years,
)

_LAMBDA = 4.5
_CATALOGUE_SIZE = 1000


@pytest.fixture
def config():
    """Simulation knobs with a year count big enough to reconcile tightly."""
    return load_frequency_config("thames").simulation


@pytest.fixture
def catalogue():
    """An event catalogue in which one event in ten floods the subject."""
    return np.random.default_rng(1).random(_CATALOGUE_SIZE) < 0.10


# --------------------------------------------------------------- arrival draws

def test_annual_counts_recover_the_arrival_rate():
    rng = np.random.default_rng(0)
    counts = simulate_annual_counts(_LAMBDA, 200_000, rng)
    assert counts.mean() == pytest.approx(_LAMBDA, rel=0.01)


def test_annual_counts_of_a_poisson_process_have_variance_near_the_mean():
    rng = np.random.default_rng(0)
    counts = simulate_annual_counts(_LAMBDA, 200_000, rng)
    assert counts.var() == pytest.approx(_LAMBDA, rel=0.05)


def test_a_negative_rate_is_treated_as_zero():
    rng = np.random.default_rng(0)
    assert simulate_annual_counts(-1.0, 100, rng).sum() == 0


def test_zero_rate_produces_no_events(config, catalogue):
    simulation = simulate_years(catalogue, 0.0, config)
    assert simulation.events_per_year.sum() == 0
    assert simulation.annual_flood_probability() == 0.0


# ------------------------------------------------------- closed-form agreement

def test_simulation_agrees_with_its_closed_form(config, catalogue):
    """The property the whole design rests on: the analytic result is the exact
    expectation of the simulation, not an approximation of it."""
    simulation = simulate_years(catalogue, _LAMBDA, config)
    within_tolerance, error = reconcile(simulation, config)

    assert within_tolerance
    assert error < 0.01


@pytest.mark.parametrize("lambda_per_year", [0.5, 2.0, 4.5, 12.0])
def test_agreement_holds_across_arrival_rates(config, catalogue, lambda_per_year):
    simulation = simulate_years(catalogue, lambda_per_year, config)
    assert reconcile(simulation, config)[0]


def test_expected_floods_match_lambda_times_p(config, catalogue):
    """The aggregate view, which a conditional-only model cannot express."""
    simulation = simulate_years(catalogue, _LAMBDA, config)
    assert simulation.expected_floods_per_year() == pytest.approx(
        analytic_expected_floods(_LAMBDA, simulation.p_event), rel=0.02)


def test_aggregate_exceeds_occurrence_when_years_can_carry_several_floods(config):
    """With a high rate and a floody catalogue, the mean number of floods per
    year must exceed the probability that a year floods at all."""
    always = np.ones(100, dtype=bool)
    simulation = simulate_years(always, 3.0, config)
    assert simulation.expected_floods_per_year() > simulation.annual_flood_probability()


def test_a_catalogue_that_always_floods_gives_the_pure_arrival_probability(config):
    """With p = 1 the annual probability collapses to 1 - exp(-lambda)."""
    always = np.ones(100, dtype=bool)
    simulation = simulate_years(always, _LAMBDA, config)
    assert simulation.annual_flood_probability() == pytest.approx(
        1.0 - np.exp(-_LAMBDA), rel=0.01)


def test_a_catalogue_that_never_floods_gives_zero(config):
    never = np.zeros(100, dtype=bool)
    simulation = simulate_years(never, _LAMBDA, config)
    assert simulation.annual_flood_probability() == 0.0
    assert reconcile(simulation, config)[0]


# ---------------------------------------------------------- analytic behaviour

def test_analytic_probability_is_monotone_in_the_arrival_rate():
    probabilities = [analytic_annual_probability(lam, 0.1) for lam in (1, 2, 4, 8)]
    assert probabilities == sorted(probabilities)


def test_analytic_probability_is_bounded():
    """At an extreme rate the probability saturates at exactly one, which is
    the correct limit rather than an overflow."""
    assert analytic_annual_probability(0.0, 0.5) == 0.0
    assert analytic_annual_probability(1.0, 0.1) < 1.0
    assert analytic_annual_probability(1e6, 0.5) == 1.0


def test_catchment_lambda_defaults_when_unnamed():
    """A run with no catchment named still gets a rate rather than failing."""
    from config.frequency import DEFAULT_LAMBDA_PER_YEAR, catchment_lambda
    assert catchment_lambda(None) == DEFAULT_LAMBDA_PER_YEAR
    assert catchment_lambda("") == DEFAULT_LAMBDA_PER_YEAR
    assert catchment_lambda("thames") == 4.5
    assert catchment_lambda("THAMES") == 4.5
    assert catchment_lambda("nowhere") == DEFAULT_LAMBDA_PER_YEAR


def test_analytic_clamps_negative_inputs():
    assert analytic_annual_probability(-1.0, 0.5) == 0.0
    assert analytic_annual_probability(1.0, -0.5) == 0.0
    assert analytic_expected_floods(-1.0, -0.5) == 0.0


def test_reconcile_flags_a_total_mismatch():
    """A simulation finding floods where the closed form allows none is a total
    failure, reported as such rather than as a small relative gap."""
    simulation = YearSimulation(
        n_years=10, lambda_per_year=0.0, p_event=0.0,
        events_per_year=np.zeros(10, dtype=np.int64),
        flood_events_per_year=np.ones(10, dtype=np.int64), seed=1)
    within_tolerance, error = reconcile(simulation, SimulationConfig())
    assert not within_tolerance
    assert error == 1.0


def test_reconcile_accepts_a_consistent_zero():
    simulation = YearSimulation(
        n_years=10, lambda_per_year=0.0, p_event=0.0,
        events_per_year=np.zeros(10, dtype=np.int64),
        flood_events_per_year=np.zeros(10, dtype=np.int64), seed=1)
    assert reconcile(simulation, SimulationConfig()) == (True, 0.0)


# ------------------------------------------------------------------ correlation

def test_shared_draws_keep_subjects_correlated(config):
    """Two gauges on the same reach flood in the same storms. One set of draws
    must serve both, or the portfolio looks far better diversified than it is."""
    rng = np.random.default_rng(1)
    upstream = rng.random(_CATALOGUE_SIZE) < 0.10
    downstream = upstream & (rng.random(_CATALOGUE_SIZE) < 0.60)

    draws = draw_event_years(_CATALOGUE_SIZE, _LAMBDA, config)
    shared = np.corrcoef(
        apply_catalogue(draws, upstream).flood_events_per_year,
        apply_catalogue(draws, downstream).flood_events_per_year)[0, 1]

    independent = np.corrcoef(
        simulate_years(upstream, _LAMBDA, config, seed=1).flood_events_per_year,
        simulate_years(downstream, _LAMBDA, config, seed=2).flood_events_per_year)[0, 1]

    assert shared > 0.5
    assert abs(independent) < 0.05


def test_every_subject_sees_the_same_arrival_counts(config, catalogue):
    draws = draw_event_years(_CATALOGUE_SIZE, _LAMBDA, config)
    other = np.random.default_rng(9).random(_CATALOGUE_SIZE) < 0.3

    first = apply_catalogue(draws, catalogue)
    second = apply_catalogue(draws, other)
    assert np.array_equal(first.events_per_year, second.events_per_year)


def test_floods_never_exceed_the_events_that_arrived(config, catalogue):
    simulation = simulate_years(catalogue, _LAMBDA, config)
    assert np.all(simulation.flood_events_per_year <= simulation.events_per_year)


# ---------------------------------------------------------------- reproducibility

def test_a_run_is_reproducible_from_its_seed(config, catalogue):
    first = simulate_years(catalogue, _LAMBDA, config, seed=99)
    second = simulate_years(catalogue, _LAMBDA, config, seed=99)
    assert np.array_equal(
        first.flood_events_per_year, second.flood_events_per_year)


def test_different_seeds_give_different_runs(config, catalogue):
    first = simulate_years(catalogue, _LAMBDA, config, seed=1)
    second = simulate_years(catalogue, _LAMBDA, config, seed=2)
    assert not np.array_equal(
        first.flood_events_per_year, second.flood_events_per_year)


def test_the_seed_used_is_recorded(config, catalogue):
    assert simulate_years(catalogue, _LAMBDA, config, seed=77).seed == 77


def test_the_configured_seed_is_the_default(config, catalogue):
    assert simulate_years(catalogue, _LAMBDA, config).seed == config.seed


# ------------------------------------------------------------------ edge cases

def test_an_empty_catalogue_produces_no_floods(config):
    simulation = simulate_years(np.zeros(0, dtype=bool), _LAMBDA, config)
    assert simulation.annual_flood_probability() == 0.0
    assert simulation.p_event == 0.0


def test_zero_years_is_inert(config, catalogue):
    simulation = simulate_years(catalogue, _LAMBDA, config, n_years=0)
    assert simulation.n_years == 0
    assert simulation.annual_flood_probability() == 0.0
    assert simulation.expected_floods_per_year() == 0.0


def test_zero_years_reports_zero_return_periods(config, catalogue):
    simulation = simulate_years(catalogue, _LAMBDA, config, n_years=0)
    assert simulation.return_period_years((2, 10)) == {2: 0.0, 10: 0.0}


def test_draws_against_an_empty_catalogue_are_empty(config):
    draws = draw_event_years(0, _LAMBDA, config, n_years=10)
    assert draws.event_indices.size == 0
    assert draws.events_per_year.sum() == 0


def test_apply_catalogue_tolerates_empty_draws(config, catalogue):
    empty = EventDraws(
        n_years=5, lambda_per_year=_LAMBDA,
        events_per_year=np.zeros(5, dtype=np.int64),
        event_indices=np.zeros(0, dtype=np.int64), seed=1)
    simulation = apply_catalogue(empty, catalogue)
    assert simulation.annual_flood_probability() == 0.0
    assert simulation.p_event == pytest.approx(float(catalogue.mean()))


# --------------------------------------------------------------- return periods

def test_return_periods_are_non_decreasing_in_severity(config):
    always = np.ones(100, dtype=bool)
    simulation = simulate_years(always, _LAMBDA, config)
    levels = simulation.return_period_years((2, 10, 50, 100))
    assert levels[2] <= levels[10] <= levels[50] <= levels[100]
