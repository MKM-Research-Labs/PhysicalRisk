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

"""One-year capital relief for a real commercial asset (WP2).

The same question as ``one_year`` -- what does a PRS do to the borrower's PD and
the bank's capital -- asked of an asset on the platform instead of the study's
illustrative borrower:

- **Years of events** are drawn with the platform's own sampler
  (``draw_event_years``): a Poisson number of events at the catchment rate,
  scaled by catalogue coverage, each event drawn by its catalogue weight.
- **Losses** come from the platform's damage ratio at the asset in each event,
  summed over the year's events and capped at the whole building. Remediation is
  the uninsured share of damage to the building; business interruption is rent
  lost for a downtime proportional to damage.
- **The PRS** is sized to the asset's uninsured flood loss: its notional is the
  uninsured loss -- uninsured repair plus lost rent -- the asset suffers in a
  typical flooding event of the catalogue. An asset that never floods gets no
  cover. It pays that notional at most once a year, when its reference gauge
  passes Severe Flood Warning in any of the year's events -- the platform's
  binary trigger. It is priced with the platform's PRS spread
  (``compute_prs_spread``) on the same catalogue's annual trigger probability.
- **The borrower** is the investor who owns the asset: net rent with a one-year
  shock, debt service from the loan, a liquidity buffer. Default is liquidity
  below zero at the year end.

**The lender pays the premium, out of the loan's spread.** The borrower's
coupon does not change. It is disaggregated: the credit spread drops by the PRS
spread, and the lender uses that slice to buy the cover. So the borrower pays
nothing extra and receives the payout, and its PD can only fall. The cost is the
lender's -- credit spread given up -- and is set against what the lender gets
back: lower expected loss and lower capital.

This differs from the study in ``one_year``, where the borrower pays the premium
from its own cash and a PRS can raise PD in the years it does not pay out.

Both cases share the same years and shocks, so the PD difference is the PRS.
"""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Optional

import numpy as np

from config.capital import STATUS, AssetRunConfig
from config.frequency import SimulationConfig
from config.loan import discount_rate
from models.frequency import annual_exceedance_probability
from models.frequency.ylt import draw_event_years
from models.hazard.prs_analytical import compute_prs_spread

from .asset_inputs import MONTHS_PER_YEAR, AssetCase
from .one_year import outcome, rate

BPS = 10_000.0
PRS_TENOR_YEARS = 1


def run(case: AssetCase, cfg: Optional[AssetRunConfig] = None) -> Dict:
    """Results, attribution and economics for one asset, with an audit record."""
    cfg = cfg or AssetRunConfig()
    inv, cap = cfg.investor, cfg.capital
    years = simulate_years(case, cfg)
    damage, triggered = years["damage"], years["triggered"]

    building = inv.building_share_of_value * case.property_value
    rent = case.annual_rent
    remediation = damage * building * (1.0 - inv.insured_share_of_damage)
    lost_rent = rent * inv.max_downtime_months * damage / MONTHS_PER_YEAR

    notional = size_notional(case, cfg)
    p_trigger = trigger_probability(case)
    spread_bps = compute_prs_spread(p_trigger, PRS_TENOR_YEARS,
                                    risk_free_rate=discount_rate(PRS_TENOR_YEARS))
    premium = notional * spread_bps / BPS
    payout = np.where(triggered, notional, 0.0)

    debt_service = case.annual_debt_service
    liquidity = inv.liquidity_months_of_debt_service * debt_service / MONTHS_PER_YEAR
    income = rent * (1.0 + inv.income_vol * years["z_income"])
    base = liquidity + income - debt_service - remediation - lost_rent
    # The premium is not the borrower's: it comes out of the lender's spread.
    default_base, default_prs = base < 0.0, base + payout < 0.0

    flooded = damage > 0.0
    no_flood_default = liquidity + income - debt_service < 0.0
    exposure = case.loan_balance
    results = {
        "without_prs": outcome(default_base, flooded, cfg.n_years, exposure, cap),
        "with_prs": outcome(default_prs, flooded, cfg.n_years, exposure, cap),
    }
    b, p = results["without_prs"], results["with_prs"]

    def capital_cost(rwa: float) -> float:
        return rwa * cap.capital_ratio * cap.cost_of_equity

    capital_saving_sa = capital_cost(b["sa_rwa"]) - capital_cost(p["sa_rwa"])
    capital_saving_irb = capital_cost(b["irb_rwa"]) - capital_cost(p["irb_rwa"])
    el_saving = b["expected_loss"] - p["expected_loss"]

    return {
        "audit": {
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "config_sha256": cfg.fingerprint(),
            "seed": cfg.seed,
            "n_years": cfg.n_years,
            "status": STATUS,
            "config": asdict(cfg),
            "asset_id": case.asset_id,
            "catchment": case.catchment,
            "reference_gauge_id": case.reference_gauge_id,
            "controlling_gauge_id": case.controlling_gauge_id,
        },
        "results": results,
        "attribution": {
            "pd_no_hazard_component": rate(no_flood_default),
            "pd_hazard_attributable": b["pd_1y"] - rate(no_flood_default),
            "p_site_flood": rate(flooded),
            "p_trigger": rate(triggered),
            "defaults_averted_by_prs": rate(default_base & ~default_prs),
            # Basis risk, both ways: a flood the PRS missed, a payout with no flood.
            "p_site_flood_but_no_payout": rate(flooded & ~triggered),
            "p_payout_but_no_site_flood": rate(triggered & ~flooded),
        },
        "economics": {
            "annual_rent": rent,
            "annual_debt_service": debt_service,
            "building_value": building,
            "prs_notional": notional,
            "prs_annual_trigger_probability": p_trigger,
            "prs_spread_bps": spread_bps,
            "prs_premium": premium,
            "bank_capital_cost_saving_sa": capital_saving_sa,
            "bank_capital_cost_saving_irb": capital_saving_irb,
            "bank_expected_loss_saving": el_saving,
            # The lender's account: spread given up for the cover, against what
            # the cover saves it. Positive means the PRS pays for itself.
            "bank_net_benefit_irb": el_saving + capital_saving_irb - premium,
            "bank_net_benefit_sa": el_saving + capital_saving_sa - premium,
        },
        "coupon": coupon_disaggregation(case, premium),
    }


def coupon_disaggregation(case: AssetCase, premium: float) -> Dict[str, float]:
    """The loan's coupon split into risk-free, credit and PRS spreads.

    The contractual rate is unchanged by the PRS; only its split moves. The PRS
    spread is the premium as a running rate on the loan balance, and the credit
    spread is whatever remains above the risk-free rate.
    """
    risk_free = discount_rate(case.remaining_term_years)
    prs_spread = premium / case.loan_balance if case.loan_balance > 0 else 0.0
    credit_before = case.interest_rate - risk_free
    return {
        "contractual_rate": case.interest_rate,
        "risk_free_rate": risk_free,
        "credit_spread_without_prs": credit_before,
        "prs_spread": prs_spread,
        "credit_spread_with_prs": credit_before - prs_spread,
    }


def uninsured_loss_per_unit_damage(case: AssetCase, cfg: AssetRunConfig) -> float:
    """Uninsured repair plus lost rent, per unit of damage ratio."""
    inv = cfg.investor
    building = inv.building_share_of_value * case.property_value
    return (building * (1.0 - inv.insured_share_of_damage)
            + case.annual_rent * inv.max_downtime_months / MONTHS_PER_YEAR)


def size_notional(case: AssetCase, cfg: AssetRunConfig) -> float:
    """The PRS notional: the asset's uninsured loss in a typical flooding event.

    The catalogue-weighted mean, over the events that flood the asset, of
    uninsured repair plus lost rent. A binary payout cannot follow the size of
    each flood, so it is set to the loss it most often has to meet. An asset
    that never floods gets a notional of zero: no cover, and no spread carved
    out of the loan for it.
    """
    flooding = case.damage_ratio > 0.0
    weight = float(case.event_weights[flooding].sum())
    if weight <= 0.0:
        return 0.0
    mean_damage = float(np.dot(case.event_weights[flooding],
                               case.damage_ratio[flooding])) / weight
    return mean_damage * uninsured_loss_per_unit_damage(case, cfg)


def simulate_years(case: AssetCase, cfg: AssetRunConfig) -> Dict[str, np.ndarray]:
    """Per simulated year: damage ratio (summed, capped at one), trigger, income shock."""
    draws = draw_event_years(
        len(case.event_ids), case.lambda_per_year * case.event_coverage,
        SimulationConfig(n_years=cfg.n_years, seed=cfg.seed),
        weights=case.event_weights)
    year_of = np.repeat(np.arange(cfg.n_years), draws.events_per_year)
    idx = draws.event_indices
    damage = np.minimum(1.0, np.bincount(
        year_of, weights=case.damage_ratio[idx], minlength=cfg.n_years))
    triggered = np.bincount(
        year_of, weights=case.triggered[idx].astype(float), minlength=cfg.n_years) > 0
    # A separate stream for the income shock, so it never shares draws with events.
    z_income = np.random.default_rng([cfg.seed, 1]).standard_normal(cfg.n_years)
    return {"damage": damage, "triggered": triggered, "z_income": z_income}


def trigger_probability(case: AssetCase) -> float:
    """Annual probability the reference gauge passes Severe, from the catalogue."""
    p_event = case.event_coverage * float(np.dot(case.event_weights, case.triggered))
    return annual_exceedance_probability(case.lambda_per_year, p_event)
