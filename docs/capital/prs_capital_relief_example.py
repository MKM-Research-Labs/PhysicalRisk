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
PRS capital-relief worked example
=================================

Question
--------
Can a Physical Risk Swap (PRS) held by a flood-exposed borrower lower that
borrower's one-year probability of default (PD) enough to move it across the
investment-grade boundary (BB+ -> BBB-), and what does that do to the lending
bank's capital?

Mechanism
---------
1. A flood (annual-maximum gauge level, GEV) damages the borrower's site.
   Damage requires remediation spend, and downtime causes lost income
   (business interruption, BI).
2. Without protection, the flood-year liquidity drain (uninsured repair + BI)
   on top of ordinary earnings volatility can exhaust liquidity -> default.
3. With a PRS, a parametric payout (on the same gauge) arrives quickly and
   funds remediation and replaces lost income. The borrower pays an annual
   premium in every state of the world, including non-flood years.
4. Both cases run on common random numbers, so the PD difference is the
   PRS effect, not simulation noise.

Scope and status
----------------
ILLUSTRATIVE. All parameters live in ``ExampleConfig`` (single source of
truth). They are chosen to represent a plausible BB+ mid-cap borrower in a
flood plain. They are NOT calibrated to observed data. The next step is to
calibrate the hazard block to Thames gauge data and the borrower block to the
mortgage/property book. The master scale and SA risk weights are also
illustrative and must be replaced with the bank's own master scale and the
applicable jurisdiction's rules (UK: PRA Basel 3.1).

Audit
-----
``run()`` returns a result dict with the config, its SHA-256 hash, the seed,
path count and a UTC timestamp, so every figure is reproducible.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone

import numpy as np
from scipy.stats import genextreme, norm


# --------------------------------------------------------------------------
# Configuration (single source of truth; all figures in GBP millions, years)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class BorrowerConfig:
    revenue: float = 50.0
    ebitda: float = 8.0                   # 16% margin
    ebitda_vol: float = 0.32              # 1y EBITDA shock vol (non-hazard)
    debt: float = 32.0                    # 4.0x leverage, all bank debt
    interest_rate: float = 0.07
    amortisation: float = 2.0
    maintenance_capex: float = 1.5
    liquidity: float = 5.0                # cash + undrawn RCF
    site_asset_value: float = 8.0         # flood-exposed plant, stock, fit-out
    contribution_margin: float = 0.40     # EBITDA lost per unit revenue lost
    insured_share_of_damage: float = 0.50 # partial cover: commercial flood cover in
                                          # high-hazard zones is often restricted


@dataclass(frozen=True)
class HazardConfig:
    # Annual-maximum gauge level (m), GEV. xi > 0 = heavy (Frechet) tail.
    gev_loc: float = 4.00
    gev_scale: float = 0.30
    gev_shape_xi: float = 0.10
    # Site floods when gauge exceeds this level; depth = slope*(L - level) + noise
    site_flood_level: float = 5.55
    depth_slope: float = 1.00
    depth_noise_sd: float = 0.15          # gauge-to-site basis risk
    damage_depth_scale: float = 0.60      # damage frac = 1 - exp(-depth/scale)
    max_downtime_months: float = 3.0      # downtime = max * damage fraction


@dataclass(frozen=True)
class PRSConfig:
    notional: float = 6.0
    attach_level: float = 5.50            # gauge level where payout starts
    exhaust_level: float = 6.05           # gauge level for full notional
    premium_loading: float = 0.50         # premium = E[payout] * (1 + loading)


@dataclass(frozen=True)
class CapitalConfig:
    lgd: float = 0.45
    maturity_years: float = 2.5
    capital_ratio: float = 0.105          # 8% + 2.5% conservation buffer
    cost_of_equity: float = 0.12
    ig_credit_spread_benefit: float = 0.0125  # borrower's BB+ -> BBB- spread
                                              # saving (illustrative 125bp)


# Illustrative master scale: (grade, upper PD bound, SA corporate risk weight)
MASTER_SCALE: tuple[tuple[str, float, float], ...] = (
    ("A-",   0.0007, 0.50),
    ("BBB+", 0.0012, 0.75),
    ("BBB",  0.0020, 0.75),
    ("BBB-", 0.0035, 0.75),
    ("BB+",  0.0060, 1.00),
    ("BB",   0.0100, 1.00),
    ("BB-",  0.0170, 1.00),
    ("B+",   0.0300, 1.50),
    ("B",    1.0000, 1.50),
)


@dataclass(frozen=True)
class ExampleConfig:
    borrower: BorrowerConfig = field(default_factory=BorrowerConfig)
    hazard: HazardConfig = field(default_factory=HazardConfig)
    prs: PRSConfig = field(default_factory=PRSConfig)
    capital: CapitalConfig = field(default_factory=CapitalConfig)
    n_paths: int = 2_000_000
    seed: int = 20260930

    def fingerprint(self) -> str:
        blob = json.dumps(asdict(self), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()


# --------------------------------------------------------------------------
# Building blocks (pure functions, individually testable)
# --------------------------------------------------------------------------
def simulate_drivers(cfg: ExampleConfig) -> dict[str, np.ndarray]:
    """Common random numbers shared by the with- and without-PRS runs."""
    rng = np.random.default_rng(cfg.seed)
    h = cfg.hazard
    n = cfg.n_paths
    return {
        "z_ebitda": rng.standard_normal(n),
        # scipy's genextreme uses c = -xi
        "gauge_level": genextreme.rvs(
            c=-h.gev_shape_xi, loc=h.gev_loc, scale=h.gev_scale,
            size=n, random_state=rng,
        ),
        "depth_noise": rng.normal(0.0, h.depth_noise_sd, n),
    }


def flood_losses(gauge_level, depth_noise, b: BorrowerConfig, h: HazardConfig):
    """Return (site depth, uninsured remediation cost, BI loss)."""
    depth = np.maximum(0.0, h.depth_slope * (gauge_level - h.site_flood_level)
                       + depth_noise)
    damage_frac = 1.0 - np.exp(-depth / h.damage_depth_scale)
    remediation = damage_frac * b.site_asset_value * (1.0 - b.insured_share_of_damage)
    downtime_months = h.max_downtime_months * damage_frac
    bi_loss = downtime_months / 12.0 * b.revenue * b.contribution_margin
    return depth, remediation, bi_loss


def prs_payout(gauge_level, p: PRSConfig) -> np.ndarray:
    """Parametric linear payout between attach and exhaust gauge levels."""
    frac = np.clip((gauge_level - p.attach_level) / (p.exhaust_level - p.attach_level),
                   0.0, 1.0)
    return p.notional * frac


def year_end_liquidity(drivers, b: BorrowerConfig, remediation, bi_loss,
                       payout, premium) -> np.ndarray:
    fixed_charges = b.debt * b.interest_rate + b.amortisation + b.maintenance_capex
    ebitda = b.ebitda * (1.0 + b.ebitda_vol * drivers["z_ebitda"])
    return (b.liquidity + ebitda - fixed_charges - premium
            - remediation - bi_loss + payout)


def irb_corporate_rw(pd: float, lgd: float, m: float) -> float:
    """Basel IRB corporate risk weight (no SME adjustment), as a fraction."""
    pd = max(pd, 0.0005)  # Basel III corporate PD floor 5bp
    e = math.exp(-50.0 * pd)
    w = (1.0 - e) / (1.0 - math.exp(-50.0))
    r = 0.12 * w + 0.24 * (1.0 - w)
    b = (0.11852 - 0.05478 * math.log(pd)) ** 2
    k = lgd * norm.cdf((norm.ppf(pd) + math.sqrt(r) * norm.ppf(0.999))
                       / math.sqrt(1.0 - r)) - pd * lgd
    k *= (1.0 + (m - 2.5) * b) / (1.0 - 1.5 * b)
    return 12.5 * k


def grade_for_pd(pd: float) -> tuple[str, float]:
    for grade, upper, sa_rw in MASTER_SCALE:
        if pd <= upper:
            return grade, sa_rw
    raise ValueError(f"PD {pd} outside master scale")


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run(cfg: ExampleConfig | None = None) -> dict:
    cfg = cfg or ExampleConfig()
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

    def pd(mask) -> float:
        return float(mask.mean())

    def cond(mask, given) -> float:
        return float(mask[given].mean()) if given.any() else float("nan")

    results = {}
    for label, dflt in (("without_prs", default_base), ("with_prs", default_prs)):
        pd_ = pd(dflt)
        grade, sa_rw = grade_for_pd(pd_)
        irb_rw = irb_corporate_rw(pd_, c.lgd, c.maturity_years)
        results[label] = {
            "pd_1y": pd_,
            "pd_std_error": math.sqrt(pd_ * (1 - pd_) / cfg.n_paths),
            "grade": grade,
            "pd_given_site_flood": cond(dflt, site_flooded),
            "pd_given_no_flood": cond(dflt, ~site_flooded),
            "sa_rw": sa_rw,
            "sa_rwa": sa_rw * b.debt,
            "irb_rw": irb_rw,
            "irb_rwa": irb_rw * b.debt,
            "expected_loss": pd_ * c.lgd * b.debt,
        }

    base, prs = results["without_prs"], results["with_prs"]

    # Default attribution (the PD decomposition regulators and agencies will ask for)
    attribution = {
        "pd_no_hazard_component": pd(no_flood_base),
        "pd_hazard_attributable": base["pd_1y"] - pd(no_flood_base),
        "p_site_flood": pd(site_flooded),
        "defaults_averted_by_prs": pd(default_base & ~default_prs),
        "defaults_caused_by_premium": pd(default_prs & ~default_base),
        # basis risk: site flooded and default persists despite PRS
        "residual_flood_defaults_with_prs": pd(default_prs & site_flooded),
        "p_site_flood_but_no_payout": pd(site_flooded & (payout == 0.0)),
    }

    # Economics (annual, GBP m). Net cost of PRS to borrower is the loading only:
    # the expected payout comes back to the borrower on average.
    def capital_cost(rwa: float) -> float:
        return rwa * c.capital_ratio * c.cost_of_equity

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
        "audit": {
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "config_sha256": cfg.fingerprint(),
            "seed": cfg.seed,
            "n_paths": cfg.n_paths,
            "status": "ILLUSTRATIVE - parameters not calibrated to observed data",
            "config": asdict(cfg),
        },
        "results": results,
        "attribution": attribution,
        "economics": economics,
    }


def notional_sweep(notionals, cfg: ExampleConfig | None = None) -> list[dict]:
    """PD, grade and premium as a function of PRS notional (sizing curve)."""
    cfg = cfg or ExampleConfig()
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


def _fmt_report(out: dict) -> str:
    r, a, e = out["results"], out["attribution"], out["economics"]
    b0, b1 = r["without_prs"], r["with_prs"]
    lines = [
        f"{'':34}{'Without PRS':>14}{'With PRS':>14}",
        f"{'1y PD':34}{b0['pd_1y']:>14.3%}{b1['pd_1y']:>14.3%}",
        f"{'Grade (illustrative scale)':34}{b0['grade']:>14}{b1['grade']:>14}",
        f"{'PD | site flooded':34}{b0['pd_given_site_flood']:>14.1%}{b1['pd_given_site_flood']:>14.1%}",
        f"{'PD | no flood':34}{b0['pd_given_no_flood']:>14.3%}{b1['pd_given_no_flood']:>14.3%}",
        f"{'SA risk weight':34}{b0['sa_rw']:>14.0%}{b1['sa_rw']:>14.0%}",
        f"{'IRB risk weight':34}{b0['irb_rw']:>14.1%}{b1['irb_rw']:>14.1%}",
        "",
        "Attribution",
        *[f"  {k:40}{v:>10.3%}" for k, v in a.items()],
        "",
        "Economics (GBP m p.a.)",
        *[f"  {k:40}{v:>10.3f}" for k, v in e.items() if k != "prs_rate_on_line"],
        f"  {'prs_rate_on_line':40}{e['prs_rate_on_line']:>10.2%}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    output = run()
    print(_fmt_report(output))
    print("\nNotional sizing (with PRS)")
    for row in notional_sweep([0, 2, 4, 6, 8]):
        print(f"  N={row['notional']:>4.0f}  PD={row['pd_1y']:.3%}  "
              f"{row['grade']:>5}  premium={row['premium']:.3f}")
    with open("prs_capital_relief_audit.json", "w") as fh:
        json.dump(output, fh, indent=2, default=float)
