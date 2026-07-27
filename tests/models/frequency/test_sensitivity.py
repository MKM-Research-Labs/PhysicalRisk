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

import pytest

from models.frequency import trend_sensitivity

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
