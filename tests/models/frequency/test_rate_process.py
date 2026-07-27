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

"""Tests for time-varying arrival rates (MKM-EF-001, Stage 6g).

The property the whole extension turns on is that it *extends* the stationary
model without contradicting it:

- **Constant rate is the pre-6g model.** ``ConstantRate`` compounds over a tenor
  to exactly ``1 - exp(-λ·T·p)``, and at one year it is the ordinary
  annualisation seam. A trend with zero growth reduces to it.
- **A trend drifts across calendar years, not Monte Carlo samples.** It is
  indexed by contract year, a single-digit horizon, so it never compounds to the
  absurd values a per-sample rate would over ten thousand replications.
- **A positive trend raises the multi-year risk**, monotonically in growth.
"""

import math

import pytest

from models.frequency import (
    ConstantRate,
    TrendRate,
    annual_exceedance_probability,
    term_exceedance_probability,
)

_P = 0.05


# ------------------------------------------------------------- ConstantRate

class TestConstantRate:

    def test_the_rate_is_the_same_every_year(self):
        rate = ConstantRate(4.5)
        assert rate.rate_at(0) == 4.5
        assert rate.rate_at(9) == 4.5

    def test_the_cumulative_rate_is_lambda_times_the_tenor(self):
        assert ConstantRate(4.5).cumulative_rate(5) == pytest.approx(22.5)

    def test_a_negative_rate_is_floored(self):
        assert ConstantRate(-1.0).rate_at(3) == 0.0
        assert ConstantRate(-1.0).cumulative_rate(5) == 0.0

    def test_zero_tenor_accumulates_nothing(self):
        assert ConstantRate(4.5).cumulative_rate(0) == 0.0


# --------------------------------------------------------------- TrendRate

class TestTrendRate:

    def test_zero_growth_reduces_to_the_constant_rate(self):
        """The reduction that makes the trend an extension, not a contradiction."""
        trend, const = TrendRate(4.5, 0.0), ConstantRate(4.5)
        assert trend.rate_at(7) == const.rate_at(7)
        assert trend.cumulative_rate(10) == pytest.approx(const.cumulative_rate(10))

    def test_a_positive_growth_compounds_across_years(self):
        trend = TrendRate(4.5, 0.02)
        assert trend.rate_at(0) == pytest.approx(4.5)
        assert trend.rate_at(10) == pytest.approx(4.5 * 1.02 ** 10)

    def test_the_cumulative_rate_is_the_geometric_sum(self):
        trend = TrendRate(4.5, 0.02)
        expected = sum(4.5 * 1.02 ** y for y in range(6))
        assert trend.cumulative_rate(6) == pytest.approx(expected)

    def test_a_drift_over_a_realistic_tenor_stays_finite(self):
        """The category error the design avoids: indexed by contract year, a
        decade of two-percent drift is a small multiple, not an overflow."""
        assert TrendRate(4.5, 0.02).rate_at(10) < 6.0

    def test_the_base_rate_is_floored(self):
        assert TrendRate(-2.0, 0.02).rate_at(4) == 0.0


# ------------------------------------------------- term exceedance probability

class TestTermExceedance:

    def test_a_constant_rate_matches_the_stationary_poisson_compounding(self):
        prob = term_exceedance_probability(ConstantRate(4.5), _P, 5)
        assert prob == pytest.approx(1.0 - math.exp(-4.5 * 5 * _P))

    def test_a_one_year_tenor_is_the_annualisation_seam(self):
        assert term_exceedance_probability(ConstantRate(4.5), _P, 1) == pytest.approx(
            annual_exceedance_probability(4.5, _P))

    def test_a_trend_raises_the_multi_year_probability(self):
        const = term_exceedance_probability(ConstantRate(4.5), _P, 10)
        trend = term_exceedance_probability(TrendRate(4.5, 0.02), _P, 10)
        assert trend > const

    def test_it_rises_monotonically_with_growth(self):
        probs = [term_exceedance_probability(TrendRate(4.5, g), _P, 10)
                 for g in (0.0, 0.01, 0.03, 0.05)]
        assert probs == sorted(probs)

    def test_a_zero_tenor_cannot_exceed(self):
        assert term_exceedance_probability(ConstantRate(4.5), _P, 0) == 0.0

    def test_the_conditional_is_clamped(self):
        """A conditional outside [0, 1] cannot push the probability out of range."""
        assert term_exceedance_probability(ConstantRate(4.5), 5.0, 3) <= 1.0
        assert term_exceedance_probability(ConstantRate(4.5), -1.0, 3) == 0.0
