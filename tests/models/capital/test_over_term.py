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

"""The same borrower over the loan term, under four cover modes."""

from dataclasses import replace

import pytest

from config.capital import COVER_MODES, CapitalReliefConfig, OverTermConfig
from models.capital import over_term

FAST = OverTermConfig(example=CapitalReliefConfig(n_paths=150_000))


@pytest.fixture(scope="module")
def fast():
    return over_term.run(FAST)["results"]


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        over_term.cumulative_pd(FAST, "quarterly")


def test_every_mode_is_reported(fast):
    assert set(fast) == set(COVER_MODES)


def test_zero_notional_all_modes_equal():
    cfg = replace(FAST, example=replace(FAST.example, prs=replace(FAST.example.prs, notional=0.0)))
    pds = {r["cumulative_pd"] for r in over_term.run(cfg)["results"].values()}
    assert len(pds) == 1


def test_year_one_identical_for_all_covered_modes_without_drift():
    res = over_term.run(replace(FAST, gev_loc_drift_per_year=0.0))["results"]
    y1 = [res[m]["marginal_default_by_year"][0]
          for m in ("one_year_only", "annual_renewal", "embedded")]
    assert max(y1) - min(y1) < 2e-4


def test_renewal_converges_to_embedded_in_benign_market():
    cfg = replace(FAST, gev_loc_drift_per_year=0.0, post_payout_premium_uplift=0.0,
                  withdrawal_prob_after_payout=0.0, hard_market_prob_per_year=0.0)
    res = over_term.run(cfg)["results"]
    assert res["annual_renewal"]["cumulative_pd"] == pytest.approx(
        res["embedded"]["cumulative_pd"], abs=2e-4)


def test_embedded_dominates_rolled_and_one_year_cover(fast):
    assert fast["embedded"]["cumulative_pd"] <= fast["annual_renewal"]["cumulative_pd"]
    assert fast["embedded"]["cumulative_pd"] < fast["one_year_only"]["cumulative_pd"]
    assert fast["one_year_only"]["cumulative_pd"] < fast["none"]["cumulative_pd"]


def test_marginal_defaults_sum_to_cumulative(fast):
    for r in fast.values():
        assert sum(r["marginal_default_by_year"]) == pytest.approx(r["cumulative_pd"], abs=1e-12)


def test_uncapped_liquidity_lets_the_borrower_build_a_buffer():
    small = replace(FAST, example=replace(FAST.example, n_paths=50_000))
    capped = over_term.cumulative_pd(small, "none")
    uncapped = over_term.cumulative_pd(replace(small, cap_liquidity_at_opening=False), "none")
    assert uncapped["cumulative_pd"] < capped["cumulative_pd"]


def test_year_one_matches_the_one_year_view():
    """Why the two views differ, pinned: they agree in year one and diverge after,
    because term liquidity carries forward and cannot rebuild above opening."""
    from models.capital import one_year
    n = 400_000
    term = over_term.cumulative_pd(
        OverTermConfig(example=CapitalReliefConfig(n_paths=n), gev_loc_drift_per_year=0.0),
        "none")
    single = one_year.run(CapitalReliefConfig(n_paths=n))["results"]["without_prs"]["pd_1y"]
    assert term["marginal_default_by_year"][0] == pytest.approx(single, abs=5e-4)
    assert term["marginal_default_by_year"][-1] > term["marginal_default_by_year"][0]
