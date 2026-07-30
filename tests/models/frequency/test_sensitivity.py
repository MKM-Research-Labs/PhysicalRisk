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

"""Tests for the climate-trend what-if (MKM-EF-001, Stage 6j).

The harness must be a faithful, non-repricing measurement of the deferred trend
reprice: the zero-growth row is the stationary baseline exactly, and a positive
growth's delta is the reprice seeding that growth would cause.
"""

import math

import pytest

from models.frequency import (
    distributional_sensitivity,
    lambda_price_distribution,
    rate_sensitivity,
    trend_sensitivity,
)

_LAMBDA = 4.5
_P = 0.03
_TENOR = 5


def test_zero_growth_is_the_stationary_baseline():
    report = trend_sensitivity(_LAMBDA, _P, _TENOR, [0.0, 0.02, 0.05])
    zero = report["rows"][0]
    assert zero["annual_growth"] == 0.0
    assert zero["term_exceedance_probability"] == pytest.approx(
        report["stationary_probability"])
    assert zero["delta_vs_stationary"] == pytest.approx(0.0)
    assert zero["relative_change"] == pytest.approx(0.0)


def test_a_positive_trend_raises_the_multi_year_probability():
    report = trend_sensitivity(_LAMBDA, _P, _TENOR, [0.0, 0.03])
    trended = report["rows"][1]
    assert trended["term_exceedance_probability"] > report["stationary_probability"]
    assert trended["delta_vs_stationary"] > 0.0
    assert trended["relative_change"] > 0.0


def test_the_reprice_rises_monotonically_with_growth():
    report = trend_sensitivity(_LAMBDA, _P, _TENOR, [0.0, 0.01, 0.03, 0.05])
    deltas = [row["delta_vs_stationary"] for row in report["rows"]]
    assert deltas == sorted(deltas)


def test_the_final_year_probability_reflects_the_drift():
    report = trend_sensitivity(_LAMBDA, _P, _TENOR, [0.0, 0.05])
    # Year-5 annual probability is higher under drift than under the flat rate.
    assert (report["rows"][1]["final_year_annual_probability"]
            > report["rows"][0]["final_year_annual_probability"])


def test_the_report_carries_its_inputs_and_a_row_per_growth():
    grid = [0.0, 0.02, 0.04]
    report = trend_sensitivity(_LAMBDA, _P, _TENOR, grid)
    assert report["lambda_per_year"] == _LAMBDA
    assert report["p_event"] == _P
    assert report["tenor_years"] == _TENOR
    assert len(report["rows"]) == len(grid)


def test_a_zero_baseline_does_not_divide_by_zero():
    """With no per-event hazard the baseline is zero; the relative change must be
    reported as zero rather than raising."""
    report = trend_sensitivity(_LAMBDA, 0.0, _TENOR, [0.0, 0.05])
    assert report["stationary_probability"] == 0.0
    assert all(row["relative_change"] == 0.0 for row in report["rows"])


# --------------------------------------------------------- rate sensitivity

class TestRateSensitivity:

    def test_the_base_factor_reproduces_the_operating_point(self):
        report = rate_sensitivity(_LAMBDA, 0.01, [0.5, 1.0, 1.5])
        base_row = next(r for r in report["rows"] if r["factor"] == 1.0)
        assert base_row["annual_probability"] == pytest.approx(report["base_probability"])
        assert base_row["relative_change"] == pytest.approx(0.0)

    def test_the_derivative_is_the_closed_form(self):
        report = rate_sensitivity(_LAMBDA, 0.02, [1.0])
        assert report["d_prob_d_lambda"] == pytest.approx(
            0.02 * math.exp(-_LAMBDA * 0.02))

    def test_the_response_is_near_proportional_when_lambda_p_is_small(self):
        """The headline finding: at a small conditional the spread tracks lambda
        almost one-for-one, so a +20% rate is roughly a +20% spread."""
        report = rate_sensitivity(_LAMBDA, 0.005, [1.2])
        assert report["rows"][0]["relative_change"] == pytest.approx(0.20, abs=0.02)

    def test_the_spread_rises_monotonically_with_the_rate(self):
        report = rate_sensitivity(_LAMBDA, 0.02, [0.5, 0.8, 1.0, 1.2, 1.5])
        spreads = [r["spread_bps"] for r in report["rows"]]
        assert spreads == sorted(spreads)

    def test_a_zero_base_does_not_divide_by_zero(self):
        report = rate_sensitivity(_LAMBDA, 0.0, [0.5, 1.5])
        assert report["base_probability"] == 0.0
        assert all(r["relative_change"] == 0.0 for r in report["rows"])


# ------------------------------------------------- distributional sensitivity

class TestDistributionalSensitivity:

    def test_alpha_zero_is_the_poisson_baseline(self):
        report = distributional_sensitivity(0.03, [0.0, 1.0])
        assert report["rows"][0]["family"] == "poisson"
        assert report["rows"][0]["prob_at_least_one"] == pytest.approx(
            report["poisson_probability"])
        assert report["rows"][0]["relative_to_poisson"] == pytest.approx(0.0)

    def test_overdispersion_lowers_the_occurrence_probability(self):
        """More clustering puts more mass at zero, so P(at least one) falls."""
        report = distributional_sensitivity(0.03, [0.0, 0.5, 1.0, 2.0])
        rels = [r["relative_to_poisson"] for r in report["rows"]]
        assert rels == sorted(rels, reverse=True)   # decreasing
        assert rels[-1] < 0.0

    def test_the_form_is_second_order_at_low_mean_counts(self):
        """The finding that matters: at a realistic rare-flood mean the
        distributional form moves the spread by only a few percent, so the rate
        dominates, not the Poisson assumption."""
        report = distributional_sensitivity(0.03, [2.0])
        assert abs(report["rows"][0]["relative_to_poisson"]) < 0.05

    def test_a_zero_mean_has_no_exceedance(self):
        report = distributional_sensitivity(0.0, [0.0, 1.0])
        assert report["poisson_probability"] == 0.0
        assert all(r["prob_at_least_one"] == 0.0 for r in report["rows"])


# ---------------------------------------------- lambda price distribution (6l)

class TestLambdaPriceDistribution:

    def _band(self, lam=4.5):
        # +-50% band expressed as P5/P50/P95 of lambda's prior.
        return [("P5", lam * 0.5), ("P50", lam), ("P95", lam * 1.5)]

    def test_the_median_row_is_the_base_spread(self):
        r = lambda_price_distribution(0.01, 4.5, self._band())
        med = next(row for row in r["rows"] if row["label"] == "P50")
        assert med["spread_bps"] == pytest.approx(r["median_spread_bps"])
        assert med["spread_rel_to_median"] == pytest.approx(0.0)

    def test_the_spread_percentiles_transform_lambda_monotonically(self):
        r = lambda_price_distribution(0.01, 4.5, self._band())
        spreads = [row["spread_bps"] for row in r["rows"]]
        assert spreads == sorted(spreads)   # P5 < P50 < P95, same order as lambda

    def test_uncertainty_passes_through_near_one_for_one(self):
        """The headline: at a small conditional a +-50% band on lambda induces a
        near +-50% band on the spread, so passthrough is close to 1."""
        r = lambda_price_distribution(0.005, 4.5, self._band())
        assert r["passthrough"] == pytest.approx(1.0, abs=0.05)

    def test_passthrough_falls_below_one_as_lambda_p_grows(self):
        """Convexity: at a larger conditional the exp curve bends, so the spread
        band is a little tighter than lambda's — passthrough drops below 1."""
        small = lambda_price_distribution(0.005, 4.5, self._band())["passthrough"]
        large = lambda_price_distribution(0.05, 4.5, self._band())["passthrough"]
        assert large < small <= 1.0 + 1e-9

    def test_a_zero_conditional_gives_a_degenerate_band(self):
        r = lambda_price_distribution(0.0, 4.5, self._band())
        assert r["median_spread_bps"] == 0.0
        assert all(row["spread_rel_to_median"] == 0.0 for row in r["rows"])
