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

"""The same borrower over the loan term: embedded PRS against rolled cover.

Does embedding the PRS in the loan for its full tenor, at a premium fixed at
origination, reduce PD more durably than cover that has to be rolled each year?

Cover modes (``config.capital.COVER_MODES``):

- ``none``: no PRS.
- ``one_year_only``: PRS in year 1 only -- how a conservative rater or IRB
  validator must treat cover with no contractual renewal right.
- ``annual_renewal``: rolled each year at the then-current price. After a payout
  the market reprices upwards and may withdraw; a market-wide hard market can
  reprice or withdraw it too; the premium also follows the hazard trend.
- ``embedded``: in the loan for the full tenor at a premium fixed at
  origination (level-pay over the expected-payout term structure), with no
  renewal risk.

Liquidity carries forward from year to year and is capped at its opening level,
so the borrower cannot build a buffer; default is liquidity below zero in any
year. Fixed charges are held flat (no amortisation benefit), which is
conservative. The gauge annual maximum is GEV with a location drift per year.

The PD here is cumulative over the term, annualised for the master scale and
the IRB formula. Both are defined on a one-year PD, and year one agrees with
``one_year``; later years default more often because liquidity does not
recover. That is why the two views report different grades.
"""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Optional

import numpy as np
from scipy.stats import genextreme

from config.capital import COVER_MODES, STATUS, OverTermConfig

from .hazard import fixed_charges, flood_losses, prs_payout
from .regulatory import grade_for_pd, irb_corporate_rw


def simulate_drivers(cfg: OverTermConfig) -> Dict[str, np.ndarray]:
    """Common random numbers for every cover mode, one row per year.

    The draw order is part of the model; see ``hazard.simulate_drivers``.
    """
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
        "u_hard_market": rng.random(cfg.tenor_years),   # one draw a year, market-wide
        "u_hm_withdraw": rng.random(shape),
    }


def cumulative_pd(cfg: OverTermConfig, mode: str, draws=None) -> Dict:
    """Cumulative and annualised PD for one cover mode over the tenor."""
    if mode not in COVER_MODES:
        raise ValueError(f"unknown mode {mode!r}")
    ex = cfg.example
    b, h, p = ex.borrower, ex.hazard, ex.prs
    d = draws if draws is not None else simulate_drivers(cfg)
    n, T = ex.n_paths, cfg.tenor_years

    payouts = prs_payout(d["gauge_level"], p)                 # (T, n) if covered
    expected_payout_by_year = payouts.mean(axis=1)            # term structure
    embedded_premium = expected_payout_by_year.mean() * (1.0 + p.premium_loading)

    liquidity = np.full(n, b.liquidity)
    alive = np.ones(n, dtype=bool)
    covered = np.ones(n, dtype=bool)          # renewal: cover still available
    paid_last_year = np.zeros(n, dtype=bool)
    fixed = fixed_charges(b)
    annual_default = []

    for t in range(T):
        _, remediation, bi = flood_losses(d["gauge_level"][t], d["depth_noise"][t], b, h)
        ebitda = b.ebitda * (1.0 + b.ebitda_vol * d["z_ebitda"][t])
        has_cover, premium, covered = _cover(
            mode, t, n, cfg, d, expected_payout_by_year, embedded_premium,
            covered, paid_last_year)

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
    grade, sa_rw = grade_for_pd(annualised)
    return {
        "mode": mode,
        "cumulative_pd": cum,
        "annualised_pd": annualised,
        "grade": grade,
        "sa_rw": sa_rw,
        "irb_rw": irb_corporate_rw(annualised, ex.capital.lgd, ex.capital.maturity_years),
        "marginal_default_by_year": annual_default,
        "embedded_level_premium": embedded_premium,
    }


def _cover(mode, t, n, cfg, d, expected_payout_by_year, embedded_premium,
           covered, paid_last_year):
    """``(has_cover, premium, covered)`` for year ``t`` under ``mode``."""
    loading = cfg.example.prs.premium_loading
    if mode == "none" or (mode == "one_year_only" and t > 0):
        return np.zeros(n, bool), np.zeros(n), covered
    if mode == "embedded":
        return np.ones(n, bool), np.full(n, embedded_premium), covered
    if mode == "one_year_only":
        return np.ones(n, bool), np.full(n, expected_payout_by_year[0] * (1.0 + loading)), covered
    # annual_renewal
    fair = expected_payout_by_year[t] * (1.0 + loading)
    premium = np.where(paid_last_year, fair * (1.0 + cfg.post_payout_premium_uplift), fair)
    if t > 0 and d["u_hard_market"][t] < cfg.hard_market_prob_per_year:
        premium = premium * cfg.hard_market_premium_multiple
        covered = covered & ~(d["u_hm_withdraw"][t] < cfg.hard_market_withdrawal_prob)
    has_cover = covered.copy()
    return has_cover, np.where(has_cover, premium, 0.0), covered


def run(cfg: Optional[OverTermConfig] = None) -> Dict:
    """Every cover mode on common random numbers, with an audit record."""
    cfg = cfg or OverTermConfig()
    draws = simulate_drivers(cfg)
    return {
        "audit": {
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "config_sha256": cfg.fingerprint(),
            "status": STATUS,
            "config": asdict(cfg),
        },
        "results": {m: cumulative_pd(cfg, m, draws) for m in COVER_MODES},
    }
