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

"""Green's XVA integrals, U = -int rate(s) D(0,s) E[profile(s)] ds.

This module is the one place the discounting convention lives. The kernel
D(0,s) depends on the funding strategy (D-01, and the correction to D-03 in
plan §10):

- ``one_bond``         D = DF(s) exp(-s_F s) S_C(s)   r_F + lambda_C (9.64-9.67)
- ``semi_replication`` D = DF(s) S_B(s) S_C(s)        r + lambda_B + lambda_C (9.55-9.59)

Every term is computed on one quadrature grid: Gauss-Legendre on the pieces
between every point where an integrand is not smooth (premium dates, curve
knots, the settlement lag, maturity, and each zero of V), so the rule is exact
to rounding on each piece.
"""

from typing import Callable, Dict

import numpy as np
from scipy.optimize import brentq

from config.xva import XvaConfig

from .exposure_analytic import gauss_legendre, profiles
from .inputs import Market, PrsTrade
from .valuation import premium_dates, value

_ROOT_SAMPLES = 33


def _value_roots(trade: PrsTrade, market: Market, lo: float, hi: float) -> list:
    """Zeros of V on [lo, hi], where V is continuous (no premium date inside)."""
    grid = np.linspace(lo, hi, _ROOT_SAMPLES)
    # Evaluate just inside the ends: V jumps at a premium date on the right.
    grid[0], grid[-1] = lo + 1e-12, hi - 1e-12
    vals = [value(trade, market.zero, t) for t in grid]
    roots = []
    for a, b, va, vb in zip(grid[:-1], grid[1:], vals[:-1], vals[1:]):
        if va * vb < 0:
            roots.append(brentq(lambda t: value(trade, market.zero, t), a, b,
                                xtol=1e-14, rtol=1e-15))
    return roots


def breakpoints(trade: PrsTrade, market: Market, lag: float) -> np.ndarray:
    """Every point in [0, T + lag] where an integrand may not be smooth."""
    horizon = trade.tenor_years + lag
    trig = trade.trigger.breakpoints()
    cuts = np.concatenate([
        [0.0, lag, trade.tenor_years, horizon],
        premium_dates(trade), market.zero.breakpoints(), trig, trig + lag,
        market.counterparty.breakpoints(), market.own.breakpoints(),
    ])
    cuts = np.unique(cuts[(cuts >= 0.0) & (cuts <= horizon)])
    roots = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b <= trade.tenor_years:
            roots += _value_roots(trade, market, a, b)
    return np.unique(np.concatenate([cuts, roots]))


def kernel(strategy: str, market: Market, cfg: XvaConfig, s: np.ndarray) -> np.ndarray:
    base = market.zero.df(s) * market.counterparty.survival(s)
    if strategy == "one_bond":
        return base * np.exp(-cfg.own_funding_spread * s)
    if strategy == "semi_replication":
        return base * market.own.survival(s)
    raise ValueError(f"unknown funding strategy {strategy!r}")


class Grid:
    """Quadrature nodes with the exposure profiles evaluated on them."""

    def __init__(self, trade: PrsTrade, market: Market, cfg: XvaConfig):
        lag = cfg.settlement_years
        self.nodes, self.weights = gauss_legendre(
            breakpoints(trade, market, lag), cfg.quadrature_nodes)
        self.profile = profiles(trade, market.zero, self.nodes, lag, cfg.quadrature_nodes)
        self.market, self.cfg = market, cfg

    def integrate(self, strategy: str, rate: np.ndarray, exposure: np.ndarray) -> float:
        k = kernel(strategy, self.market, self.cfg, self.nodes)
        return -float(np.sum(self.weights * rate * k * exposure))


def adjustments(grid: Grid) -> Dict[str, Dict[str, float]]:
    """Both funding-strategy views; the booked one is chosen by the caller."""
    m, cfg, s, p = grid.market, grid.cfg, grid.nodes, grid.profile
    lgd_c, lgd_b = 1.0 - cfg.counterparty_recovery, 1.0 - cfg.own_recovery
    lam_c, lam_b = m.counterparty.hazard(s), m.own.hazard(s)
    s_f = np.full_like(s, cfg.own_funding_spread)

    ob = {"cva": grid.integrate("one_bond", lgd_c * lam_c, p["epe"]),
          "fva": grid.integrate("one_bond", s_f, p["ee"])}
    sr = {"cva": grid.integrate("semi_replication", lgd_c * lam_c, p["epe"]),
          "dva": grid.integrate("semi_replication", lgd_b * lam_b, p["ene"]),
          "fca": grid.integrate("semi_replication", lgd_b * lam_b, p["epe"])}
    ob["total"] = ob["cva"] + ob["fva"]
    sr["total"] = sr["cva"] + sr["dva"] + sr["fca"]
    return {"one_bond": ob, "semi_replication": sr}


def kva(grid: Grid, strategy: str, capital: Callable[[np.ndarray], np.ndarray]) -> float:
    """KVA = -int (gamma_K - phi r(s)) D E[K(s)] ds (13.25) for a capital profile.

    The capital profile itself is WP3 (SA-CCR, BA-CVA); this is the integral.
    """
    s = grid.nodes
    rate = grid.cfg.cost_of_capital - grid.cfg.capital_funding_fraction * grid.market.zero.forward_rate(s)
    return grid.integrate(strategy, rate, capital(s))
