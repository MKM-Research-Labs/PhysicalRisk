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

"""Tests for loss-weighted year sampling (MKM-EF-001, Stage 6).

Four things are pinned:

- **The aggregation is exactly right on a hand-built case.** A year's aggregate
  loss is the sum of its drawn events' losses and its occurrence loss is their
  maximum, checked against draws laid out by hand so the vectorised path cannot
  hide an off-by-one at a year boundary.
- **The closed form is the simulation's expectation.** The average annual loss
  from the run matches ``lambda_effective * weighted-mean-loss`` within sampling
  error — the loss analogue of the occurrence reconciliation, and the property
  the whole loss layer rests on.
- **AEP dominates OEP.** The aggregate loss at a return period is never below
  the single-occurrence loss, because a sum is never less than its maximum.
- **Shared draws keep subjects correlated.** Two subjects scored against the
  same draws share the storms that hit them; scoring against independent draws
  throws that away.
"""

import numpy as np
import pytest

from config.frequency import SimulationConfig, load_frequency_config
from models.frequency.datastructures import EventDraws, LossSimulation
from models.frequency.ylt import (
    analytic_average_annual_loss,
    apply_catalogue_losses,
    draw_event_years,
    loss_standard_error,
    reconcile_losses,
    simulate_losses,
)

_LAMBDA = 4.5
_CATALOGUE_SIZE = 500


@pytest.fixture
def config():
    """Simulation knobs with a year count big enough to reconcile tightly."""
    return load_frequency_config("thames").simulation


@pytest.fixture
def losses():
    """A per-event loss catalogue with a fat right tail."""
    return np.random.default_rng(1).gamma(2.0, 50.0, _CATALOGUE_SIZE)


@pytest.fixture
def weights():
    """Uniform sampling weights over the catalogue, summing to one."""
    return np.full(_CATALOGUE_SIZE, 1.0 / _CATALOGUE_SIZE)


# ------------------------------------------------------- hand-built aggregation

def _draws(events_per_year, event_indices, n_years):
    return EventDraws(
        n_years=n_years,
        lambda_per_year=2.0,
        events_per_year=np.array(events_per_year, dtype=np.int64),
        event_indices=np.array(event_indices, dtype=np.int64),
        seed=0,
    )


def test_aggregate_loss_sums_each_years_events():
    # Three years: two events, none, then one. Losses index into [10, 20, 30].
    losses = np.array([10.0, 20.0, 30.0])
    draws = _draws([2, 0, 1], [0, 2, 1], n_years=3)
    sim = apply_catalogue_losses(draws, losses)
    assert list(sim.aggregate_loss_per_year) == [40.0, 0.0, 20.0]


def test_max_event_loss_is_the_largest_in_the_year():
    losses = np.array([10.0, 20.0, 30.0])
    draws = _draws([2, 0, 1], [0, 2, 1], n_years=3)
    sim = apply_catalogue_losses(draws, losses)
    # Year 0 drew events 0 and 2 (losses 10, 30); year 1 none; year 2 event 1.
    assert list(sim.max_event_loss_per_year) == [30.0, 0.0, 20.0]


def test_an_empty_catalogue_yields_zero_losses(config):
    sim = simulate_losses(np.array([]), _LAMBDA, config)
    assert sim.average_annual_loss() == 0.0
    assert sim.aggregate_loss_per_year.sum() == 0.0


def test_a_zero_rate_produces_no_losses(config, losses):
    sim = simulate_losses(losses, 0.0, config)
    assert sim.aggregate_loss_per_year.sum() == 0.0
    assert sim.max_event_loss_per_year.sum() == 0.0


# ------------------------------------------------------- closed-form agreement

def test_average_annual_loss_agrees_with_its_closed_form(config, losses, weights):
    """The property the loss layer rests on: the run's mean aggregate loss is an
    estimate of ``lambda_effective * weighted-mean-loss``, its exact
    expectation, so the gap is sampling error and nothing else."""
    lambda_eff = _LAMBDA * 0.3
    sim = simulate_losses(losses, lambda_eff, config, weights=weights)
    within, sigmas = reconcile_losses(sim, lambda_eff, weights, losses, config)
    assert within
    assert sigmas < config.reconciliation_sigmas


@pytest.mark.parametrize("lambda_eff", [0.5, 1.35, 4.5, 9.0])
def test_agreement_holds_across_arrival_rates(config, losses, weights, lambda_eff):
    sim = simulate_losses(losses, lambda_eff, config, weights=weights)
    assert reconcile_losses(sim, lambda_eff, weights, losses, config)[0]


def test_closed_form_aal_is_rate_times_weighted_mean_loss(weights, losses):
    expected = 1.35 * float(np.dot(weights, losses))
    assert analytic_average_annual_loss(1.35, weights, losses) == pytest.approx(expected)


def test_closed_form_handles_a_degenerate_input():
    assert analytic_average_annual_loss(4.5, [], []) == 0.0
    assert analytic_average_annual_loss(4.5, [0.5, 0.5], [10.0]) == 0.0


def test_loss_standard_error_is_zero_without_years():
    assert loss_standard_error(4.5, [1.0], [10.0], 0) == 0.0


def test_reconcile_flags_a_tampered_run(config, losses, weights):
    """A run whose losses are inflated after the fact must fail the gate — the
    check has teeth, it is not satisfied by any run at all."""
    lambda_eff = _LAMBDA * 0.3
    sim = simulate_losses(losses, lambda_eff, config, weights=weights)
    tampered = LossSimulation(
        n_years=sim.n_years,
        lambda_per_year=sim.lambda_per_year,
        aggregate_loss_per_year=sim.aggregate_loss_per_year * 1.5,
        max_event_loss_per_year=sim.max_event_loss_per_year,
        seed=sim.seed,
    )
    assert not reconcile_losses(tampered, lambda_eff, weights, losses, config)[0]


# ---------------------------------------------------------------- AEP / OEP

def test_aep_dominates_oep(config, losses, weights):
    """A year's aggregate loss is never below its largest single occurrence, so
    the AEP curve sits at or above the OEP curve at every return period."""
    sim = simulate_losses(losses, _LAMBDA, config, weights=weights)
    periods = (2, 10, 50, 100, 200)
    aep, oep = sim.aep_curve(periods), sim.oep_curve(periods)
    for rp in periods:
        assert aep[rp] >= oep[rp]


def test_exceedance_curves_increase_with_return_period(config, losses, weights):
    sim = simulate_losses(losses, _LAMBDA, config, weights=weights)
    aep = sim.aep_curve((2, 10, 100, 200))
    values = [aep[rp] for rp in (2, 10, 100, 200)]
    assert values == sorted(values)


def test_exceedance_probability_is_monotone(config, losses, weights):
    sim = simulate_losses(losses, _LAMBDA, config, weights=weights)
    assert (sim.aggregate_exceedance_probability(10.0)
            >= sim.aggregate_exceedance_probability(1000.0))
    assert (sim.occurrence_exceedance_probability(10.0)
            >= sim.occurrence_exceedance_probability(1000.0))


def test_curves_of_an_empty_run_are_zero(config):
    sim = simulate_losses(np.array([]), _LAMBDA, config)
    assert sim.aep_curve((10, 100)) == {10: 0.0, 100: 0.0}
    assert sim.oep_curve((10, 100)) == {10: 0.0, 100: 0.0}
    assert sim.aggregate_exceedance_probability(0.0) == 0.0
    assert sim.occurrence_exceedance_probability(0.0) == 0.0


# ------------------------------------------------------------- shared draws

def test_shared_draws_correlate_subjects(config, weights):
    """Two subjects scored against the same draws are correlated through the
    events they share; scored against independent draws they are not. This is
    the loss-side statement of the design's shared-draw property."""
    rng = np.random.default_rng(7)
    losses_a = rng.gamma(2.0, 50.0, _CATALOGUE_SIZE)
    losses_b = 0.8 * losses_a + rng.gamma(2.0, 10.0, _CATALOGUE_SIZE)
    lambda_eff = _LAMBDA * 0.3

    shared = draw_event_years(_CATALOGUE_SIZE, lambda_eff, config, weights=weights)
    sim_a = apply_catalogue_losses(shared, losses_a)
    sim_b = apply_catalogue_losses(shared, losses_b)
    shared_corr = np.corrcoef(
        sim_a.aggregate_loss_per_year, sim_b.aggregate_loss_per_year)[0, 1]

    independent = draw_event_years(
        _CATALOGUE_SIZE, lambda_eff, config, seed=config.seed + 1, weights=weights)
    sim_b_indep = apply_catalogue_losses(independent, losses_b)
    independent_corr = np.corrcoef(
        sim_a.aggregate_loss_per_year, sim_b_indep.aggregate_loss_per_year)[0, 1]

    assert shared_corr > 0.5
    assert abs(independent_corr) < 0.1


def test_seed_pins_the_run(config, losses, weights):
    a = simulate_losses(losses, _LAMBDA, config, weights=weights)
    b = simulate_losses(losses, _LAMBDA, config, weights=weights)
    assert np.array_equal(a.aggregate_loss_per_year, b.aggregate_loss_per_year)


# ------------------------------------------------------------- a zero-year run

def _zero_year_run():
    """A run of no years — the degenerate case a portfolio with n_years=0 hits.

    Distinct from an empty *catalogue*, whose run still has the configured year
    count with every year at zero loss.
    """
    return LossSimulation(
        n_years=0,
        lambda_per_year=_LAMBDA,
        aggregate_loss_per_year=np.zeros(0),
        max_event_loss_per_year=np.zeros(0),
        seed=0,
    )


def test_a_zero_year_run_reports_zero_everywhere():
    sim = _zero_year_run()
    assert sim.average_annual_loss() == 0.0
    assert sim.aggregate_exceedance_probability(0.0) == 0.0
    assert sim.occurrence_exceedance_probability(0.0) == 0.0


def test_reconcile_of_a_zero_year_run_cannot_agree_with_a_positive_loss(
        config, losses, weights):
    """With no sampling variation, a run showing no loss where the closed form
    expects one has not merely drifted — it is wrong, so the deviation is
    infinite rather than a comfortable small number."""
    within, deviation = reconcile_losses(
        _zero_year_run(), _LAMBDA * 0.3, weights, losses, config)
    assert not within
    assert deviation == np.inf


def test_reconcile_of_a_zero_year_run_agrees_when_no_loss_is_expected(config):
    """The matching side of the same branch: no years and no expected loss
    reconcile exactly."""
    within, deviation = reconcile_losses(
        _zero_year_run(), _LAMBDA, [1.0], [0.0], config)
    assert within
    assert deviation == 0.0
