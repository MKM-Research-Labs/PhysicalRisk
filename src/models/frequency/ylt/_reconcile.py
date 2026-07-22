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


def reconcile(
    simulation: YearSimulation,
    config: SimulationConfig,
) -> Tuple[bool, float]:
    """Check a simulated annual probability against its closed form.

    Args:
        simulation: the completed run.
        config: simulation knobs supplying the tolerance.

    Returns:
        ``(within_tolerance, relative_error)``. When the closed form is zero the
        error is reported as zero if the simulation also produced zero, and as
        one otherwise — a simulation finding floods where the closed form allows
        none is a total failure, not a small relative one.
    """
    simulated = simulation.annual_flood_probability()
    expected = analytic_annual_probability(
        simulation.lambda_per_year, simulation.p_event)

    if expected == 0.0:
        error = 0.0 if simulated == 0.0 else 1.0
    else:
        error = abs(simulated - expected) / expected

    return error <= config.reconciliation_tolerance, error
