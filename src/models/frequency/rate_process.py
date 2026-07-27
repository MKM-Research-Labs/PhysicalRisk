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

"""Time-varying arrival rates for the Event Frequency Model (MKM-EF-001, 6g).

Stages 1–6f treat the arrival rate λ as a constant, which is a stationarity
assumption recorded as a model limitation: it cannot express a rate that drifts
with the climate over the life of a multi-year contract.

This is the extension point §4.14 reserved. A ``RateProcess`` gives λ as a
function of **calendar year** over a contract tenor, so a T-year contract can
compound distinct annual rates λ₀, λ₁, …, λ_{T-1} instead of one λ repeated.

Where it does *not* belong is the Monte Carlo year sampler. Those N draws are
independent replications of the *same* calendar year — the sample index is not a
timeline — so a rate that drifts with the sample index is a category error (it
compounds to absurd values over ten thousand replications). Non-stationarity is
a term-structure concern: each calendar year has one scalar rate, and the tenor
is where distinct years compose. The single-year probability therefore still
goes through the ordinary ``annual_exceedance_probability`` seam at
``process.rate_at(year)``; only the multi-year survival is new here.

The default remains stationary. ``ConstantRate`` is the pre-6g model, and
``TrendRate`` with zero growth reduces to it exactly, so nothing reprices until
a catchment is deliberately given a trend — a model-risk decision, not a
default. Within-year seasonality (a rate cycling by month) is out of scope: the
model prices in whole years, and a seasonal rate integrated over a year returns
the annual total.
"""

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class RateProcess(Protocol):
    """An arrival rate as a function of calendar year over a contract tenor."""

    def rate_at(self, year: int) -> float:
        """Return the arrival rate in calendar *year* (zero-based from tenor start)."""
        ...

    def cumulative_rate(self, n_years: int) -> float:
        """Return the total expected events over years ``0 .. n_years-1``."""
        ...


@dataclass(frozen=True)
class ConstantRate:
    """A stationary rate — the same λ every year, i.e. the pre-6g model.

    Attributes:
        lambda_per_year: the constant arrival rate; negatives floored at zero,
            matching the scalar sampler.
    """

    lambda_per_year: float

    def rate_at(self, year: int) -> float:
        """Return the constant rate, the same in every year."""
        return max(0.0, self.lambda_per_year)

    def cumulative_rate(self, n_years: int) -> float:
        """Return ``λ · n_years`` — the stationary Poisson-compounding total."""
        return max(0.0, self.lambda_per_year) * max(0, n_years)


@dataclass(frozen=True)
class TrendRate:
    """A geometrically drifting rate: ``λ_t = λ₀ · (1 + growth)^t``.

    A non-homogeneous rate across calendar years — the shape a climate trend
    takes when each year compounds on the last. Zero growth reduces to
    ``ConstantRate`` exactly, so the trend extends the model rather than
    contradicting it. Indexed by contract year (a small horizon, single digits),
    never by Monte Carlo sample.

    Attributes:
        base_lambda_per_year: the tenor-start rate ``λ₀``; negatives floored.
        annual_growth: fractional change per year. ``0.0`` is stationary;
            ``0.02`` is two percent more events each year.
    """

    base_lambda_per_year: float
    annual_growth: float

    def rate_at(self, year: int) -> float:
        """Return ``λ₀ · (1 + growth)^year``, floored at zero."""
        base = max(0.0, self.base_lambda_per_year)
        return max(0.0, base * (1.0 + self.annual_growth) ** max(0, year))

    def cumulative_rate(self, n_years: int) -> float:
        """Return the summed rate over ``0 .. n_years-1`` (a geometric series)."""
        return sum(self.rate_at(year) for year in range(max(0, n_years)))


def term_exceedance_probability(
    process: RateProcess, p_event: float, n_years: int
) -> float:
    """Return P(at least one exceedance over an *n_years* contract).

    For a non-homogeneous Poisson process the survival over the tenor is the
    product of the per-year survivals, ``∏ exp(-λ_y·p) = exp(-p·Σλ_y)``, so the
    exceedance probability is ``1 - exp(-p · cumulative_rate)``. With a
    ``ConstantRate`` this is exactly the stationary ``1 - exp(-λ·T·p)``, which is
    the reduction that keeps the trend a strict extension of the existing model.

    Args:
        process: the arrival-rate process.
        p_event: the per-event conditional exceedance probability.
        n_years: the contract tenor in years.

    Returns:
        A probability in ``[0, 1]``.
    """
    p = min(1.0, max(0.0, p_event))
    exponent = process.cumulative_rate(n_years) * p
    return 1.0 - math.exp(-max(0.0, exponent))
