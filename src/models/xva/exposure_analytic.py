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

"""Expected exposure of one PRS under deterministic flood hazard (plan §3.2).

With the trigger intensity deterministic, V(s) given no trigger is a number,
so the only randomness is the trigger time tau_E. At a future date s the trade
is in one of two states:

- not yet triggered, with probability S_E(s), worth V(s);
- triggered at u in (s - lag, s] and not yet settled, worth the pending
  payout, density lambda_E(u) S_E(u).

Hence, exactly,

    E[V(s)^+] = S_E(s) V(s)^+ + int_{max(0,s-lag)}^{min(s,T)} f_E(u) P(u, s)^+ du

with P the pending payout, which has the sign of the trade direction. The
inner integral is evaluated by Gauss-Legendre on pieces where its integrand is
smooth, so it is exact to rounding.
"""

from typing import Dict

import numpy as np

from .curves import ZeroCurve
from .inputs import PrsTrade
from .valuation import pending_payout, value


def gauss_legendre(edges: np.ndarray, n_nodes: int):
    """Nodes and weights covering [edges[0], edges[-1]], n_nodes per piece."""
    x, w = np.polynomial.legendre.leggauss(n_nodes)
    a, b = edges[:-1, None], edges[1:, None]
    nodes = (0.5 * (b - a) * x + 0.5 * (a + b)).ravel()
    weights = (0.5 * (b - a) * w).ravel()
    return nodes, weights


def _pieces(lo: float, hi: float, cuts: np.ndarray) -> np.ndarray:
    inner = cuts[(cuts > lo) & (cuts < hi)]
    return np.unique(np.concatenate([[lo], inner, [hi]]))


def pending(trade: PrsTrade, zero: ZeroCurve, s: float, lag: float, n_nodes: int) -> float:
    """Expected pending-payout value at s (signed with the trade direction)."""
    lo, hi = max(0.0, s - lag), min(s, trade.tenor_years)
    if lag <= 0.0 or hi <= lo:
        return 0.0
    cuts = np.concatenate([trade.trigger.breakpoints(), zero.breakpoints() - lag])
    u, w = gauss_legendre(_pieces(lo, hi, cuts), n_nodes)
    density = trade.trigger.hazard(u) * trade.trigger.survival(u)
    return float(np.sum(w * density * pending_payout(trade, zero, u, s, lag)))


def profile(trade: PrsTrade, zero: ZeroCurve, s: float, lag: float,
            n_nodes: int) -> Dict[str, float]:
    """EPE, ENE and EE at s: E[V^+], E[V^-] and E[V] (Green's notation)."""
    pre = value(trade, zero, s) * float(trade.trigger.survival(s)) if s < trade.tenor_years else 0.0
    post = pending(trade, zero, s, lag, n_nodes)
    return {
        "epe": max(pre, 0.0) + max(post, 0.0),
        "ene": min(pre, 0.0) + min(post, 0.0),
        "ee": pre + post,
    }


def profiles(trade: PrsTrade, zero: ZeroCurve, times: np.ndarray, lag: float,
             n_nodes: int) -> Dict[str, np.ndarray]:
    rows = [profile(trade, zero, float(s), lag, n_nodes) for s in times]
    return {key: np.array([r[key] for r in rows]) for key in ("epe", "ene", "ee")}
