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

"""One-year capital relief for a real asset, on the platform's event years."""

from dataclasses import replace

import numpy as np
import pytest

from config.capital import AssetRunConfig, InvestorConfig
from models.capital import asset_one_year

from ._asset_fixtures import make_case

FAST = AssetRunConfig(n_years=200_000)


def _run(case, cfg=FAST):
    return asset_one_year.run(case, cfg)


def test_a_well_aligned_prs_lowers_pd():
    """The asset floods exactly when the reference gauge triggers: no basis risk."""
    # A rare flood (about 3% a year), so the premium is affordable in dry years.
    case = make_case([0.0, 0.0, 0.9], [False, False, True], lam=0.1, rent_yield=0.045)
    out = _run(case)
    r = out["results"]
    assert r["with_prs"]["pd_1y"] < r["without_prs"]["pd_1y"]
    assert out["attribution"]["p_site_flood_but_no_payout"] == 0.0
    assert out["economics"]["bank_capital_cost_saving_irb"] > 0.0


def test_a_site_that_never_floods_gets_no_cover():
    """Sized to the uninsured flood loss, which is zero: no notional, no premium,
    no spread carved out of the loan, nothing changes."""
    case = make_case([0.0, 0.0, 0.0], [False, False, True], rent_yield=0.045)
    out = _run(case)
    r, e, c = out["results"], out["economics"], out["coupon"]
    assert e["prs_notional"] == 0.0 and e["prs_premium"] == 0.0
    assert r["with_prs"]["pd_1y"] == r["without_prs"]["pd_1y"]
    assert c["prs_spread"] == 0.0
    assert c["credit_spread_with_prs"] == c["credit_spread_without_prs"]
    assert e["bank_net_benefit_irb"] == 0.0


def test_notional_is_the_mean_uninsured_loss_of_a_flooding_event():
    """Weighted over the events that flood the asset; dry events do not dilute it."""
    case = make_case([0.0, 0.2, 0.6], [False, True, True], weights=[0.5, 0.3, 0.2])
    mean_damage = (0.3 * 0.2 + 0.2 * 0.6) / (0.3 + 0.2)
    building = 0.60 * 10_000_000.0
    per_unit = building * 0.5 + 0.06 * 10_000_000.0 * 3.0 / 12.0
    assert asset_one_year.size_notional(case, FAST) == pytest.approx(mean_damage * per_unit)
    assert asset_one_year.uninsured_loss_per_unit_damage(case, FAST) == pytest.approx(per_unit)


def test_the_borrower_never_pays_the_premium():
    """The premium comes out of the lender's spread, so the PRS can only add
    cash to the borrower: no year defaults with it that would not without it."""
    case = make_case([0.0, 0.3, 0.9], [True, False, True], lam=2.0, rent_yield=0.045)
    r = _run(case)["results"]
    assert r["with_prs"]["pd_1y"] <= r["without_prs"]["pd_1y"]


def test_the_coupon_is_disaggregated_not_increased():
    case = make_case([0.0, 0.9], [False, True], lam=0.2)
    out = _run(case)
    c = out["coupon"]
    assert c["contractual_rate"] == case.interest_rate
    assert (c["risk_free_rate"] + c["credit_spread_with_prs"] + c["prs_spread"]
            == pytest.approx(c["contractual_rate"]))
    assert c["prs_spread"] == pytest.approx(out["economics"]["prs_premium"] / case.loan_balance)
    assert c["credit_spread_with_prs"] < c["credit_spread_without_prs"]


def test_no_loan_balance_means_no_prs_spread():
    case = make_case([0.0], [True], balance=0.0)
    assert asset_one_year.coupon_disaggregation(case, 1_000.0)["prs_spread"] == 0.0


def test_lender_net_benefit_is_savings_less_premium():
    case = make_case([0.0, 0.9], [False, True], lam=0.2, rent_yield=0.045)
    e = _run(case)["economics"]
    assert e["bank_net_benefit_irb"] == pytest.approx(
        e["bank_expected_loss_saving"] + e["bank_capital_cost_saving_irb"] - e["prs_premium"])
    assert e["bank_net_benefit_sa"] == pytest.approx(
        e["bank_expected_loss_saving"] + e["bank_capital_cost_saving_sa"] - e["prs_premium"])


def test_no_trigger_means_no_premium_and_no_change():
    case = make_case([0.0, 0.5, 0.0], [False, False, False])
    out = _run(case)
    assert out["economics"]["prs_annual_trigger_probability"] == 0.0
    r = out["results"]
    assert r["with_prs"]["pd_1y"] == r["without_prs"]["pd_1y"]


def test_pd_moves_only_through_the_payout():
    case = make_case([0.0, 0.6, 0.9], [False, True, True], rent_yield=0.045)
    out = _run(case)
    a = out["attribution"]
    base = out["results"]["without_prs"]["pd_1y"]
    prs = out["results"]["with_prs"]["pd_1y"]
    assert prs == pytest.approx(base - a["defaults_averted_by_prs"], abs=1e-12)
    assert (a["pd_no_hazard_component"] + a["pd_hazard_attributable"]
            == pytest.approx(base))


def test_trigger_probability_follows_the_platform_rule():
    """1 - exp(-lambda * coverage * weighted share of triggering events)."""
    case = make_case([0, 0, 0, 0], [True, False, False, True],
                     weights=[0.1, 0.2, 0.3, 0.4], lam=4.0, coverage=0.5)
    expected = 1.0 - np.exp(-4.0 * 0.5 * (0.1 + 0.4))
    assert asset_one_year.trigger_probability(case) == pytest.approx(expected)


def test_simulated_trigger_rate_matches_the_catalogue():
    case = make_case([0, 0, 0, 0], [True, False, False, True],
                     weights=[0.1, 0.2, 0.3, 0.4], lam=4.0, coverage=0.5)
    years = asset_one_year.simulate_years(case, FAST)
    assert years["triggered"].mean() == pytest.approx(
        asset_one_year.trigger_probability(case), abs=4e-3)


def test_annual_damage_is_capped_at_the_whole_building():
    """Several large floods in one year cannot destroy more than one building."""
    case = make_case([0.9], [False], lam=6.0)
    years = asset_one_year.simulate_years(case, AssetRunConfig(n_years=20_000))
    assert years["damage"].max() == 1.0
    assert years["damage"].min() >= 0.0


def test_payout_is_at_most_once_a_year():
    """The trigger is a yes/no per year, however many events pass Severe."""
    case = make_case([0.5], [True], lam=6.0)
    years = asset_one_year.simulate_years(case, AssetRunConfig(n_years=20_000))
    assert years["triggered"].dtype == bool


def test_reproducible_and_audited():
    case = make_case([0.0, 0.5], [False, True])
    a, b = _run(case), _run(case)
    assert a["results"] == b["results"]
    audit = a["audit"]
    for key in ("run_utc", "config_sha256", "seed", "n_years", "status", "config",
                "asset_id", "catchment", "reference_gauge_id", "controlling_gauge_id"):
        assert key in audit
    other = replace(FAST, investor=replace(FAST.investor, income_vol=0.2))
    assert other.fingerprint() != FAST.fingerprint()


def test_bigger_liquidity_buffer_lowers_pd():
    case = make_case([0.0, 0.8], [False, True], rent_yield=0.045)
    thin = _run(case, replace(FAST, investor=InvestorConfig(liquidity_months_of_debt_service=1)))
    thick = _run(case, replace(FAST, investor=InvestorConfig(liquidity_months_of_debt_service=24)))
    assert (thick["results"]["without_prs"]["pd_1y"]
            < thin["results"]["without_prs"]["pd_1y"])


def test_default_config_is_used_when_none_given():
    out = asset_one_year.run(make_case([0.0], [False]))
    assert out["audit"]["config_sha256"] == AssetRunConfig().fingerprint()
    assert out["audit"]["n_years"] == AssetRunConfig().n_years
