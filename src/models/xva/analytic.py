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

"""The analytic XVA engine (WP1): one gauge PRS, deterministic flood hazard,
counterparty and bank defaults independent of flood, uncollateralised.

``run`` returns the risk-free value, both funding-strategy views with the
booked one marked (D-01), the break-even all-in spread, the exposure profiles
on a reporting grid, and an audit record. Sign convention (Green): an
adjustment below zero is a cost to the bank.
"""

from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Dict, Optional

import numpy as np
from scipy.optimize import brentq

from config.xva import STATUS, XvaConfig

from .exposure_analytic import profiles
from .inputs import Market, PrsTrade
from .integrals import Grid, adjustments
from .valuation import fair_spread, legs, value

_BPS = 1e4


def xva(trade: PrsTrade, market: Market, cfg: XvaConfig) -> Dict[str, Dict[str, float]]:
    """Both views of U for the trade as booked."""
    return adjustments(Grid(trade, market, cfg))


def break_even_spread(trade: PrsTrade, market: Market, cfg: XvaConfig) -> float:
    """The spread at which risk-free value plus booked XVA is zero to the bank.

    This is the exact all-in quote. The plan's s* - U / (N A) is its
    first-order approximation, which ignores that U moves with the spread.
    """
    def all_in(spread: float) -> float:
        t = replace(trade, spread=spread)
        return value(t, market.zero, 0.0) + xva(t, market, cfg)[cfg.funding_strategy]["total"]

    s_fair = fair_spread(trade, market.zero)
    width = max(s_fair, 1e-4)
    lo, hi = s_fair - width, s_fair + width
    while all_in(lo) * all_in(hi) > 0:
        width *= 2.0
        lo, hi = s_fair - width, s_fair + width
        if width > 10.0:
            raise ValueError("no break-even spread within 1000 percent of the fair spread")
    return brentq(all_in, lo, hi, xtol=1e-12, rtol=1e-12)


def run(trade: PrsTrade, market: Market, cfg: Optional[XvaConfig] = None,
        solve_spread: bool = True) -> Dict:
    cfg = cfg or XvaConfig()
    views = xva(trade, market, cfg)
    leg = legs(trade, market.zero, 0.0)
    s_fair = fair_spread(trade, market.zero)
    horizon = trade.tenor_years + cfg.settlement_years
    times = np.arange(0.0, horizon + 1e-12, cfg.profile_step_years)
    prof = profiles(trade, market.zero, times, cfg.settlement_years, cfg.quadrature_nodes)

    result = {
        "value": value(trade, market.zero, 0.0),
        "fair_spread_bps": s_fair * _BPS,
        "trade_spread_bps": trade.spread * _BPS,
        "risky_annuity": leg["annuity"],
        "views": views,
        "booked_strategy": cfg.funding_strategy,
        "booked": views[cfg.funding_strategy],
        "dva_disclosed": views["semi_replication"]["dva"],
        "profiles": {"t": times.tolist(), **{k: v.tolist() for k, v in prof.items()}},
        "audit": audit_record(trade, cfg),
    }
    if solve_spread:
        s_all_in = break_even_spread(trade, market, cfg)
        result["all_in_spread_bps"] = s_all_in * _BPS
        result["xva_spread_bps"] = (s_all_in - s_fair) * _BPS
    return result


def audit_record(trade: PrsTrade, cfg: XvaConfig) -> Dict:
    return {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": "analytic",
        "config_sha256": cfg.fingerprint(),
        "status": STATUS,
        "config": asdict(cfg),
        "trade": {"notional": trade.notional, "spread": trade.spread,
                  "tenor_years": trade.tenor_years,
                  "bank_buys_protection": trade.bank_buys_protection},
    }
