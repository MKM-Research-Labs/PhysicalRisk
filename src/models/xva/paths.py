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

"""The simulation grid, the hazard-factor paths and trade values on them.

Time integration is the midpoint rule on cells that never straddle a premium
date, a maturity or the end of a settlement lag (D-14). V jumps only at those
dates, so inside a cell the integrand is smooth apart from the path's own
trigger, and the trigger time is continuous, so sampling it at a midpoint is
unbiased: a cell's midpoint falls inside a settlement window with probability
(window / cell), and it then carries the whole cell's weight.
"""

from typing import Dict

import numpy as np

from .cir import CirFactor, ShiftedTrigger
from .curves import ZeroCurve
from .inputs import PrsTrade
from .netting import NettingSet
from .valuation import QUARTER, premium_dates


def grid(nset: NettingSet, lag: float, cells_per_quarter: int):
    """Cell midpoints and widths covering [0, horizon + lag]."""
    horizon = nset.horizon + lag
    cuts = [0.0, horizon]
    for t in nset.trades:
        cuts += list(premium_dates(t)) + [t.tenor_years, t.tenor_years + lag]
    cuts = np.unique(np.clip(cuts, 0.0, horizon))
    nodes, widths = [], []
    target = QUARTER / cells_per_quarter
    for a, b in zip(cuts[:-1], cuts[1:]):
        n = max(1, int(np.ceil((b - a) / target - 1e-9)))
        edges = np.linspace(a, b, n + 1)
        nodes.append(0.5 * (edges[:-1] + edges[1:]))
        widths.append(np.diff(edges))
    return np.concatenate(nodes), np.concatenate(widths)


def factor_paths(factor: CirFactor, times: np.ndarray, n_paths: int,
                 rng: np.random.Generator):
    """Y on ``times`` (which start at 0, where Y = 1) and the clock C(t) = int_0^t Y.

    Y steps exactly (noncentral chi-square); the clock is the trapezoid rule
    on ``times``, exact when sigma = 0.
    """
    if times[0] != 0.0:
        raise ValueError("simulation times must start at 0")
    y = np.ones((n_paths, times.size))
    for k in range(1, times.size):
        y[:, k] = factor.step(y[:, k - 1], times[k] - times[k - 1], rng)
    increments = 0.5 * (y[:, 1:] + y[:, :-1]) * np.diff(times)
    clock = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(increments, axis=1)], axis=1)
    return y, clock


def alive_value(trade: PrsTrade, trigger: ShiftedTrigger, zero: ZeroCurve, t: float,
                y: np.ndarray) -> np.ndarray:
    """V(t) per path given Y(t) = y and no trigger by t (closed form, CIR++)."""
    dates = premium_dates(trade)
    ends = dates[dates > t]
    if ends.size == 0 or t >= trade.tenor_years:
        return np.zeros_like(y)
    starts = np.maximum(ends - QUARTER, t)
    s_start = trigger.survival(t, starts, y)
    s_end = trigger.survival(t, ends, y)
    df_t = float(zero.df(t))
    protection = (s_start - s_end) @ (zero.df(0.5 * (starts + ends)) / df_t)
    annuity = s_end @ (QUARTER * zero.df(ends) / df_t)
    return trade.direction * trade.notional * (protection - trade.spread * annuity)


def trade_values(trade: PrsTrade, trigger: ShiftedTrigger, zero: ZeroCurve,
                 at: np.ndarray, y_at: np.ndarray, first_trigger: np.ndarray,
                 lag: float) -> np.ndarray:
    """(n_paths, len(at)) value of one trade: alive, pending payout, or nothing."""
    out = np.zeros((first_trigger.size, at.size))
    settles = first_trigger + lag
    for k, t in enumerate(at):
        alive = first_trigger > t
        if t < trade.tenor_years and np.any(alive):
            out[alive, k] = alive_value(trade, trigger, zero, t, y_at[alive, k])
        pending = (~alive) & (t < settles) & (first_trigger <= trade.tenor_years)
        if np.any(pending):
            out[pending, k] = (trade.direction * trade.notional
                               * zero.df(settles[pending]) / zero.df(t))
    return out


def lookup(times: np.ndarray, values: np.ndarray, at: np.ndarray) -> np.ndarray:
    """Columns of ``values`` (simulated on ``times``) at the exact times ``at``."""
    idx = np.searchsorted(times, at)
    if not np.allclose(times[np.clip(idx, 0, times.size - 1)], at, atol=1e-12):
        raise ValueError("requested time is not on the simulation grid")
    return values[:, idx]


def simulation_times(nodes: np.ndarray, lagged: np.ndarray, horizon: float) -> np.ndarray:
    return np.unique(np.concatenate([[0.0], nodes, lagged, [horizon]]))


def triggers_for(nset: NettingSet, factor: CirFactor) -> Dict[str, ShiftedTrigger]:
    return {gauge: ShiftedTrigger(factor, curve) for gauge, curve in nset.gauges.items()}
