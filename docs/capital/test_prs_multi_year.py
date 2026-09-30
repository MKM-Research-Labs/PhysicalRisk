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

"""Tests for prs_multi_year (run: pytest -q)."""

from dataclasses import replace

import pytest

import prs_capital_relief_example as base
import prs_multi_year as mm

FAST = mm.MultiYearConfig(example=base.ExampleConfig(n_paths=150_000))


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        mm.cumulative_pd(FAST, "quarterly")


def test_zero_notional_all_modes_equal():
    cfg = replace(FAST, example=replace(FAST.example, prs=replace(FAST.example.prs, notional=0.0)))
    res = mm.run(cfg)["results"]
    pds = {r["cumulative_pd"] for r in res.values()}
    assert len(pds) == 1


def test_year_one_identical_for_all_covered_modes_without_drift():
    cfg = replace(FAST, gev_loc_drift_per_year=0.0)
    res = mm.run(cfg)["results"]
    y1 = [res[m]["marginal_default_by_year"][0] for m in ("one_year_only", "annual_renewal", "embedded")]
    assert max(y1) - min(y1) < 2e-4


def test_renewal_converges_to_embedded_in_benign_market():
    cfg = replace(FAST, gev_loc_drift_per_year=0.0, post_payout_premium_uplift=0.0,
                  withdrawal_prob_after_payout=0.0, hard_market_prob_per_year=0.0)
    res = mm.run(cfg)["results"]
    assert res["annual_renewal"]["cumulative_pd"] == pytest.approx(
        res["embedded"]["cumulative_pd"], abs=2e-4)


def test_embedded_dominates_rolled_and_one_year_cover():
    res = mm.run(FAST)["results"]
    assert res["embedded"]["cumulative_pd"] <= res["annual_renewal"]["cumulative_pd"]
    assert res["embedded"]["cumulative_pd"] < res["one_year_only"]["cumulative_pd"]
    assert res["one_year_only"]["cumulative_pd"] < res["none"]["cumulative_pd"]


def test_marginal_defaults_sum_to_cumulative():
    for r in mm.run(FAST)["results"].values():
        assert sum(r["marginal_default_by_year"]) == pytest.approx(r["cumulative_pd"], abs=1e-12)
