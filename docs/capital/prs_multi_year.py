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

"""
Multi-year extension: embedded (term-matched) PRS vs rolled cover
=================================================================

Question
--------
Does embedding the PRS in the loan for its full tenor, at a premium fixed at
origination, deliver a more durable PD reduction than cover that must be
rolled annually?

Cover modes compared over the loan tenor
----------------------------------------
- "none"            : no PRS.
- "one_year_only"   : PRS in year 1 only. This is how a conservative rater or
                      IRB validator must treat cover with no contractual
                      renewal right.
- "annual_renewal"  : PRS rolled each year at the then-current price. After a
                      payout the market reprices the cover upwards and may
                      withdraw it altogether; the premium also follows the
                      hazard trend.
- "embedded"        : PRS embedded in the loan for the full tenor, premium
                      fixed at origination (level-pay over the tenor's
                      expected-payout term structure), no renewal risk.

Dynamics
--------
Liquidity carries forward year to year. Default = liquidity < 0 in any year.
The gauge annual maximum is i.i.d. GEV with a location drift per year
(hazard trend). Fixed charges are held flat (no amortisation benefit), which
is conservative. Reuses every building block from prs_capital_relief_example
(single source of truth for borrower, hazard, PRS and capital parameters).

ILLUSTRATIVE — parameters not calibrated to observed data.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np
from scipy.stats import genextreme

import prs_capital_relief_example as base

MODES = ("none", "one_year_only", "annual_renewal", "embedded")


@dataclass(frozen=True)
class MultiYearConfig:
    example: base.ExampleConfig = field(default_factory=lambda: base.ExampleConfig(n_paths=1_000_000))
    tenor_years: int = 5
    gev_loc_drift_per_year: float = 0.01   # m/yr rise in annual-max gauge level
    post_payout_premium_uplift: float = 1.0  # rolled premium x(1+uplift) after a payout
    withdrawal_prob_after_payout: float = 0.30  # market withdraws cover after a payout
    # Market-wide hard market (e.g. after a regional catastrophe elsewhere):
    # rolled cover reprices for everyone or capacity withdraws. Not borrower-specific.
    hard_market_prob_per_year: float = 0.10
    hard_market_premium_multiple: float = 3.0
    hard_market_withdrawal_prob: float = 0.25
    # Surplus cash above opening liquidity is distributed/reinvested (steady state)
    cap_liquidity_at_opening: bool = True

    def fingerprint(self) -> str:
        import hashlib
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def _draws(cfg: MultiYearConfig) -> dict[str, np.ndarray]:
    ex, h = cfg.example, cfg.example.hazard
    rng = np.random.default_rng(ex.seed)
    shape = (cfg.tenor_years, ex.n_paths)
    locs = h.gev_loc + cfg.gev_loc_drift_per_year * np.arange(cfg.tenor_years)[:, None]
    return {
        "z_ebitda": rng.standard_normal(shape),
        "gauge_level": genextreme.rvs(c=-h.gev_shape_xi, loc=locs, scale=h.gev_scale,
                                      size=shape, random_state=rng),
        "depth_noise": rng.normal(0.0, h.depth_noise_sd, shape),
        "u_withdraw": rng.random(shape),
        "u_hard_market": rng.random(cfg.tenor_years),   # one draw per year, market-wide
        "u_hm_withdraw": rng.random(shape),
    }


def cumulative_pd(cfg: MultiYearConfig, mode: str, draws=None) -> dict:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    ex = cfg.example
    b, h, p = ex.borrower, ex.hazard, ex.prs
    d = draws if draws is not None else _draws(cfg)
    n, T = ex.n_paths, cfg.tenor_years

    payouts = base.prs_payout(d["gauge_level"], p)            # (T, n) if covered
    expected_payout_by_year = payouts.mean(axis=1)             # term structure
    embedded_premium = expected_payout_by_year.mean() * (1.0 + p.premium_loading)

    liquidity = np.full(n, b.liquidity)
    alive = np.ones(n, dtype=bool)
    covered = np.ones(n, dtype=bool)          # renewal: cover still available
    paid_last_year = np.zeros(n, dtype=bool)
    fixed = b.debt * b.interest_rate + b.amortisation + b.maintenance_capex
    annual_default = []

    for t in range(T):
        _, remediation, bi = base.flood_losses(d["gauge_level"][t], d["depth_noise"][t], b, h)
        ebitda = b.ebitda * (1.0 + b.ebitda_vol * d["z_ebitda"][t])

        if mode == "none" or (mode == "one_year_only" and t > 0):
            has_cover, premium = np.zeros(n, bool), np.zeros(n)
        elif mode == "embedded":
            has_cover, premium = np.ones(n, bool), np.full(n, embedded_premium)
        elif mode == "one_year_only":
            has_cover = np.ones(n, bool)
            premium = np.full(n, expected_payout_by_year[0] * (1.0 + p.premium_loading))
        else:  # annual_renewal
            fair = expected_payout_by_year[t] * (1.0 + p.premium_loading)
            premium = np.where(paid_last_year, fair * (1.0 + cfg.post_payout_premium_uplift), fair)
            if t > 0 and d["u_hard_market"][t] < cfg.hard_market_prob_per_year:
                premium = premium * cfg.hard_market_premium_multiple
                covered &= ~(d["u_hm_withdraw"][t] < cfg.hard_market_withdrawal_prob)
            has_cover = covered.copy()
            premium = np.where(has_cover, premium, 0.0)

        payout = np.where(has_cover, payouts[t], 0.0)
        liquidity = liquidity + ebitda - fixed - premium - remediation - bi + payout
        if cfg.cap_liquidity_at_opening:
            liquidity = np.minimum(liquidity, b.liquidity)
        newly_defaulted = alive & (liquidity < 0.0)
        annual_default.append(float(newly_defaulted.mean()))
        alive &= ~newly_defaulted

        if mode == "annual_renewal":
            paid_last_year = payout > 0.0
            covered &= ~(paid_last_year & (d["u_withdraw"][t] < cfg.withdrawal_prob_after_payout))

    cum = 1.0 - float(alive.mean())
    annualised = 1.0 - (1.0 - cum) ** (1.0 / T)
    grade, sa_rw = base.grade_for_pd(annualised)
    return {
        "mode": mode,
        "cumulative_pd": cum,
        "annualised_pd": annualised,
        "grade": grade,
        "sa_rw": sa_rw,
        "irb_rw": base.irb_corporate_rw(annualised, ex.capital.lgd, ex.capital.maturity_years),
        "marginal_default_by_year": annual_default,
        "embedded_level_premium": embedded_premium,
    }


def run(cfg: MultiYearConfig | None = None) -> dict:
    cfg = cfg or MultiYearConfig()
    draws = _draws(cfg)  # common random numbers across all modes
    return {
        "audit": {
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "config_sha256": cfg.fingerprint(),
            "status": "ILLUSTRATIVE - parameters not calibrated to observed data",
            "config": asdict(cfg),
        },
        "results": {m: cumulative_pd(cfg, m, draws) for m in MODES},
    }


if __name__ == "__main__":
    out = run()
    print(f"{'Mode':18}{'Cum PD 5y':>11}{'Annualised':>12}{'Grade':>7}{'SA RW':>7}{'IRB RW':>8}")
    for m, r in out["results"].items():
        print(f"{m:18}{r['cumulative_pd']:>11.3%}{r['annualised_pd']:>12.3%}"
              f"{r['grade']:>7}{r['sa_rw']:>7.0%}{r['irb_rw']:>8.1%}")
    print(f"\nEmbedded level premium: GBP {out['results']['embedded']['embedded_level_premium']:.3f}m p.a.")
    with open("prs_multi_year_audit.json", "w") as fh:
        json.dump(out, fh, indent=2, default=float)
