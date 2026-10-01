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

"""One-year capital relief: the borrower's PD with and without a PRS.

A flood on the gauge damages the borrower's site, costing uninsured remediation
and lost income. Without protection that drain, on top of ordinary earnings
volatility, can exhaust liquidity: default. The PRS pays on the same gauge,
funding the remediation and replacing the income, for a premium paid in every
year whether or not it floods. Both cases run on common random numbers, so the
PD difference is the PRS, not simulation noise.

The PD here is a one-year PD, which is what the master scale and the IRB formula
are defined on. See ``over_term`` for the same borrower over the loan term.
"""

import math
from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np

from config.capital import STATUS, CapitalConfig, CapitalReliefConfig

from .hazard import flood_losses, prs_payout, simulate_drivers, year_end_liquidity
from .regulatory import grade_for_pd, irb_corporate_rw


def run(cfg: Optional[CapitalReliefConfig] = None) -> Dict:
    """Results, default attribution and economics, with an audit record."""
    cfg = cfg or CapitalReliefConfig()
    b, h, p, c = cfg.borrower, cfg.hazard, cfg.prs, cfg.capital

    d = simulate_drivers(cfg)
    depth, remediation, bi_loss = flood_losses(d["gauge_level"], d["depth_noise"], b, h)
    payout = prs_payout(d["gauge_level"], p)
    expected_payout = float(payout.mean())
    premium = expected_payout * (1.0 + p.premium_loading)

    zero = np.zeros_like(payout)
    liq_base = year_end_liquidity(d, b, remediation, bi_loss, zero, 0.0)
    liq_prs = year_end_liquidity(d, b, remediation, bi_loss, payout, premium)
    default_base, default_prs = liq_base < 0.0, liq_prs < 0.0

    site_flooded = depth > 0.0
    no_flood_base = year_end_liquidity(d, b, zero, zero, zero, 0.0) < 0.0

    results = {
        "without_prs": outcome(default_base, site_flooded, cfg.n_paths, b.debt, c),
        "with_prs": outcome(default_prs, site_flooded, cfg.n_paths, b.debt, c),
    }
    base, prs = results["without_prs"], results["with_prs"]

    # The PD decomposition regulators and rating agencies will ask for.
    attribution = {
        "pd_no_hazard_component": rate(no_flood_base),
        "pd_hazard_attributable": base["pd_1y"] - rate(no_flood_base),
        "p_site_flood": rate(site_flooded),
        "defaults_averted_by_prs": rate(default_base & ~default_prs),
        "defaults_caused_by_premium": rate(default_prs & ~default_base),
        # Basis risk: the site flooded and the default persists despite the PRS.
        "residual_flood_defaults_with_prs": rate(default_prs & site_flooded),
        "p_site_flood_but_no_payout": rate(site_flooded & (payout == 0.0)),
    }

    def capital_cost(rwa: float) -> float:
        return rwa * c.capital_ratio * c.cost_of_equity

    # Annual, GBP m. The net cost of the PRS to the borrower is the loading only:
    # the expected payout comes back to the borrower on average.
    economics = {
        "prs_expected_payout": expected_payout,
        "prs_premium": premium,
        "prs_rate_on_line": premium / p.notional if p.notional > 0 else 0.0,
        "prs_net_cost_loading": premium - expected_payout,
        "bank_capital_cost_saving_sa": capital_cost(base["sa_rwa"]) - capital_cost(prs["sa_rwa"]),
        "bank_capital_cost_saving_irb": capital_cost(base["irb_rwa"]) - capital_cost(prs["irb_rwa"]),
        "bank_expected_loss_saving": base["expected_loss"] - prs["expected_loss"],
        "borrower_funding_saving_if_ig": (
            c.ig_credit_spread_benefit * b.debt
            if base["grade"].startswith("BB") and prs["grade"].startswith("BBB") else 0.0
        ),
    }

    return {
        "audit": audit_record(cfg),
        "results": results,
        "attribution": attribution,
        "economics": economics,
    }


def audit_record(cfg: CapitalReliefConfig) -> Dict:
    """What makes a figure reproducible: the config, its hash, seed and path count."""
    return {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_sha256": cfg.fingerprint(),
        "seed": cfg.seed,
        "n_paths": cfg.n_paths,
        "status": STATUS,
        "config": asdict(cfg),
    }


def notional_sweep(notionals, cfg: Optional[CapitalReliefConfig] = None) -> List[Dict]:
    """PD, grade and premium as a function of PRS notional (the sizing curve)."""
    cfg = cfg or CapitalReliefConfig()
    rows = []
    for n in notionals:
        out = run(replace(cfg, prs=replace(cfg.prs, notional=float(n))))
        rows.append({
            "notional": float(n),
            "pd_1y": out["results"]["with_prs"]["pd_1y"],
            "grade": out["results"]["with_prs"]["grade"],
            "premium": out["economics"]["prs_premium"],
        })
    return rows


def outcome(defaulted: np.ndarray, site_flooded: np.ndarray, n_paths: int,
            exposure: float, c: CapitalConfig) -> Dict:
    """PD, grade, risk weights and expected loss for one case's defaults.

    Shared with ``asset_one_year``, so both report a case the same way.
    """
    pd = rate(defaulted)
    grade, sa_rw = grade_for_pd(pd)
    irb_rw = irb_corporate_rw(pd, c.lgd, c.maturity_years)
    return {
        "pd_1y": pd,
        "pd_std_error": math.sqrt(pd * (1 - pd) / n_paths),
        "grade": grade,
        "pd_given_site_flood": _conditional(defaulted, site_flooded),
        "pd_given_no_flood": _conditional(defaulted, ~site_flooded),
        "sa_rw": sa_rw,
        "sa_rwa": sa_rw * exposure,
        "irb_rw": irb_rw,
        "irb_rwa": irb_rw * exposure,
        "expected_loss": pd * c.lgd * exposure,
    }


def rate(mask: np.ndarray) -> float:
    return float(mask.mean())


def _conditional(mask: np.ndarray, given: np.ndarray) -> float:
    return float(mask[given].mean()) if given.any() else float("nan")
