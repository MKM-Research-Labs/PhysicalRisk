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

"""The annualisation seam for the Event Frequency Model (MKM-EF-001).

The one place a per-event conditional becomes an annual probability. Frequency
logic must not leak into the event simulator or the pricing modules; the
composition happens here.

Why the closed form rather than the Monte Carlo, for this particular output:
the hazard curve needs a single scalar per gauge and trigger, and for that
scalar the closed form is not an approximation of the simulation but its exact
expectation (see ``ylt/_reconcile.py``), computed instantly and with no
sampling noise. The simulation earns its keep where the closed form has nothing
to say — the annual *distribution*, occurrence versus aggregate views, and
return-period levels — and those come from ``ylt/``.
"""

import math
from typing import List

from .rate_process import RateProcess


def annual_exceedance_probability(lambda_per_year: float, p_event: float) -> float:
    """Return P(at least one exceedance in a year).

    For a Poisson number of events N with rate lambda, each exceeding
    independently with probability p, ``E[(1-p)^N] = exp(-lambda*p)``, so the
    probability of at least one exceedance is ``1 - exp(-lambda*p)``.

    Args:
        lambda_per_year: the catchment event arrival rate.
        p_event: the per-event conditional exceedance probability.

    Returns:
        An annual probability in ``[0, 1]``. Non-positive inputs give zero.
    """
    exponent = max(0.0, lambda_per_year) * max(0.0, p_event)
    return 1.0 - math.exp(-exponent)


def annual_exceedance_rate(lambda_per_year: float, p_event: float) -> float:
    """Return the expected number of exceedances per year.

    The aggregate view. It exceeds the occurrence probability whenever a year
    can carry more than one exceedance — the case a conditional-only model
    cannot represent at all.

    Args:
        lambda_per_year: the catchment event arrival rate.
        p_event: the per-event conditional exceedance probability.

    Returns:
        Exceedances per year.
    """
    return max(0.0, lambda_per_year) * max(0.0, p_event)


def return_period_years(lambda_per_year: float, p_event: float) -> float:
    """Return the mean interval between exceedances.

    Args:
        lambda_per_year: the catchment event arrival rate.
        p_event: the per-event conditional exceedance probability.

    Returns:
        Years between exceedances, or infinity when the rate is zero.
    """
    rate = annual_exceedance_rate(lambda_per_year, p_event)
    return float("inf") if rate <= 0 else 1.0 / rate


def annual_hazard_by_year(
    process: RateProcess, p_event: float, max_years: int
) -> List[float]:
    """Return the annual exceedance probability for each year of a tenor.

    Year ``y``'s value is ``annual_exceedance_probability(λ_y, p)`` where
    ``λ_y`` is the arrival rate the *process* gives for that year. Under a
    ``ConstantRate`` every year is identical and this is a flat list, which is
    what keeps a non-stationary term structure a strict generalisation of the
    stationary one (MKM-EF-001, Stage 6h).

    These are the per-year hazards the multi-year term structure compounds. They
    follow the platform's existing convention — the annual *probability* used as
    the per-year hazard — rather than the exact ``1 - exp(-p·Σλ)`` of
    ``term_exceedance_probability``, so that wiring a flat (stationary) process
    reproduces the current term structure exactly.

    Args:
        process: the arrival-rate process over the tenor.
        p_event: the per-event conditional exceedance probability.
        max_years: the tenor length in years.

    Returns:
        A list of *max_years* annual exceedance probabilities, year 1 first.
    """
    return [
        annual_exceedance_probability(process.rate_at(year), p_event)
        for year in range(max(0, max_years))
    ]
