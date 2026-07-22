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

"""Closed-form reconciliation for the year simulation (MKM-EF-001).

The Monte Carlo is the engine; this is its self-test.

For a Poisson number of events N with rate lambda, each flooding independently
with probability p:

    E[(1-p)^N] = exp(lambda * ((1-p) - 1)) = exp(-lambda * p)

so P(at least one flood in a year) = 1 - exp(-lambda * p) *exactly*. The closed
form is not an approximation of the simulation — it is the simulation's
expectation. Any gap beyond sampling error means one of the two is wrong, which
makes this a genuine check rather than a restatement.

The same argument gives the aggregate view directly: E[floods per year] is
lambda * p.
"""

import math
from typing import Tuple

from config.frequency import SimulationConfig

from ..datastructures import YearSimulation


def analytic_annual_probability(lambda_per_year: float, p_event: float) -> float:
    """Return the exact annual flood probability under a Poisson arrival process.

    Args:
        lambda_per_year: the catchment arrival rate.
        p_event: the per-event conditional flood probability.

    Returns:
        ``1 - exp(-lambda * p)``, clamped at zero for non-positive inputs.
    """
    exponent = max(0.0, lambda_per_year) * max(0.0, p_event)
    return 1.0 - math.exp(-exponent)


def analytic_expected_floods(lambda_per_year: float, p_event: float) -> float:
    """Return the exact mean number of flooding events per year.

    Args:
        lambda_per_year: the catchment arrival rate.
        p_event: the per-event conditional flood probability.

    Returns:
        ``lambda * p``.
    """
    return max(0.0, lambda_per_year) * max(0.0, p_event)


def sampling_standard_error(probability: float, n_years: int) -> float:
    """Return the standard error of an annual probability estimated from a run.

    Each simulated year is a Bernoulli trial on "did this year flood", so the
    estimate's standard error is the usual ``sqrt(p(1-p)/n)``.

    Args:
        probability: the annual flood probability.
        n_years: number of years simulated.

    Returns:
        The standard error, or ``0.0`` when there is no sampling variation to
        speak of (no years, or a probability pinned at zero or one).
    """
    if n_years <= 0:
        return 0.0
    return math.sqrt(max(0.0, probability * (1.0 - probability)) / n_years)


def reconcile(
    simulation: YearSimulation,
    config: SimulationConfig,
) -> Tuple[bool, float]:
    """Check a simulated annual probability against its closed form.

    The gap is measured in sampling standard errors rather than as a fixed
    percentage. The simulation is a finite sample, so it is *expected* to miss
    its own expectation by roughly one standard error; a fixed percentage band
    either false-alarms at low year counts or stops binding at high ones. In
    standard errors the gate means the same thing at every ``n_years``.

    Args:
        simulation: the completed run.
        config: simulation knobs supplying the allowed number of sigmas.

    Returns:
        ``(within_tolerance, deviation_in_standard_errors)``. When there is no
        sampling variation the deviation is zero if the two agree exactly and
        infinite otherwise — a simulation finding floods where the closed form
        allows none has not drifted, it is wrong.
    """
    simulated = simulation.annual_flood_probability()
    expected = analytic_annual_probability(
        simulation.lambda_per_year, simulation.p_event)

    standard_error = sampling_standard_error(expected, simulation.n_years)
    if standard_error == 0.0:
        deviation = 0.0 if simulated == expected else math.inf
    else:
        deviation = abs(simulated - expected) / standard_error

    return deviation <= config.reconciliation_sigmas, deviation
