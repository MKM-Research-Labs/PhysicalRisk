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

"""Discount and hazard curves for the XVA model.

``ZeroCurve`` reproduces the PRS pricer's discounting exactly: zero rates
linear between integer-year knots, flat outside them, DF(t) = exp(-r(t) t)
(``models.hazard.prs_analytical.interpolate_yield_rate``). ``HazardCurve`` is
piecewise-constant, the reduced-form default model Green uses (Ch. 4); the
same class carries the flood trigger, the counterparty and the bank.
"""

import math
from typing import Dict, Iterable, Optional, Sequence

import numpy as np
from scipy.optimize import brentq

from models.hazard.prs_analytical import interpolate_yield_rate

_QUARTER = 0.25


class ZeroCurve:
    """Continuously compounded zero curve on the pricer's yield-curve dict."""

    def __init__(self, yield_curve: Optional[Dict[str, float]] = None,
                 flat_rate: float = 0.03):
        if yield_curve:
            keys = sorted(int(k) for k in yield_curve)
            self.knots = np.array(keys, dtype=float)
            self.rates = np.array([yield_curve[str(k)] for k in keys], dtype=float)
        else:
            self.knots = np.array([0.0])
            self.rates = np.array([flat_rate])
        self._source = dict(yield_curve) if yield_curve else None
        self._flat = flat_rate

    def zero_rate(self, t):
        return np.interp(t, self.knots, self.rates)

    def df(self, t):
        t = np.asarray(t, dtype=float)
        return np.exp(-self.zero_rate(t) * t)

    def forward_rate(self, t):
        """Instantaneous forward f(t) = d(r(t) t)/dt, the short rate in Green's KVA."""
        t = np.asarray(t, dtype=float)
        slopes = np.diff(self.rates) / np.diff(self.knots) if len(self.knots) > 1 else np.array([])
        idx = np.searchsorted(self.knots, t, side="right") - 1
        inside = (idx >= 0) & (idx < len(slopes))
        slope = np.where(inside, slopes[np.clip(idx, 0, max(len(slopes) - 1, 0))]
                         if len(slopes) else 0.0, 0.0)
        return self.zero_rate(t) + t * slope

    def pricer_rate(self, t: float) -> float:
        """The rate the pricer itself would use at t (for reconciliation tests)."""
        return interpolate_yield_rate(self._source, t, self._flat) if self._source else self._flat

    def breakpoints(self) -> np.ndarray:
        return self.knots.copy()


class HazardCurve:
    """Piecewise-constant intensity: rates[k] applies on (knots[k-1], knots[k]].

    ``knots`` are the right ends of the segments; the last rate extends flat
    beyond the last knot.
    """

    def __init__(self, knots: Sequence[float], rates: Sequence[float]):
        self.knots = np.asarray(knots, dtype=float)
        self.rates = np.asarray(rates, dtype=float)
        if len(self.knots) != len(self.rates) or len(self.rates) == 0:
            raise ValueError("knots and rates must be non-empty and the same length")
        if np.any(np.diff(self.knots) <= 0) or self.knots[0] <= 0:
            raise ValueError("knots must be positive and strictly increasing")
        if np.any(self.rates < 0):
            raise ValueError("hazard rates must be non-negative")
        starts = np.concatenate([[0.0], self.knots[:-1]])
        self._starts = starts
        self._cum = np.concatenate([[0.0], np.cumsum(self.rates[:-1] * np.diff(
            np.concatenate([[0.0], self.knots]))[:-1])])

    @classmethod
    def flat(cls, rate: float) -> "HazardCurve":
        return cls([1.0], [rate])

    @classmethod
    def from_annual_probability(cls, p: float) -> "HazardCurve":
        """The pricer's conversion: lambda = -ln(1 - p), p capped at 0.999."""
        return cls.flat(-math.log(1.0 - min(p, 0.999)) if p > 0 else 0.0)

    def _segment(self, t):
        return np.clip(np.searchsorted(self.knots, t, side="left"), 0, len(self.rates) - 1)

    def hazard(self, t):
        return self.rates[self._segment(np.asarray(t, dtype=float))]

    def integrated(self, t):
        t = np.asarray(t, dtype=float)
        k = self._segment(t)
        return self._cum[k] + self.rates[k] * (t - self._starts[k])

    def survival(self, t):
        return np.exp(-self.integrated(t))

    def breakpoints(self) -> np.ndarray:
        return self.knots[:-1].copy()


def cds_par_spread(hazard: HazardCurve, zero: ZeroCurve, tenor: float,
                   recovery: float) -> float:
    """Par spread on the pricer's convention: quarterly, no accrual on default,
    protection discounted at mid-period (``compute_prs_spread``)."""
    n = int(round(tenor / _QUARTER))
    t = _QUARTER * np.arange(1, n + 1)
    s = hazard.survival(t)
    s_prev = hazard.survival(t - _QUARTER)
    annuity = float(np.sum(_QUARTER * s * zero.df(t)))
    protection = float(np.sum((1.0 - recovery) * (s_prev - s) * zero.df(t - _QUARTER / 2)))
    return protection / annuity


def bootstrap_cds(tenors: Iterable[float], spreads: Iterable[float], recovery: float,
                  zero: ZeroCurve) -> HazardCurve:
    """Piecewise-constant hazard that reprices each par spread exactly (Green 4.14).

    Segments end at the quoted tenors; each is solved in turn holding the
    earlier ones fixed.
    """
    tenors, spreads = list(tenors), list(spreads)
    if sorted(tenors) != tenors or len(set(tenors)) != len(tenors):
        raise ValueError("tenors must be strictly increasing")
    rates = []
    for i, (tenor, spread) in enumerate(zip(tenors, spreads)):
        def error(rate, i=i, tenor=tenor, spread=spread):
            curve = HazardCurve(tenors[:i + 1], rates + [rate])
            return cds_par_spread(curve, zero, tenor, recovery) - spread
        if error(0.0) > 0:
            raise ValueError(f"spread {spread} at {tenor}y is below the minimum admissible")
        hi = 1.0
        while error(hi) < 0:
            hi *= 2.0
        rates.append(brentq(error, 0.0, hi, xtol=1e-15, rtol=1e-15))
    return HazardCurve(tenors, rates)


def flat_cds_curve(spread: float, recovery: float, zero: ZeroCurve,
                   tenor: float = 5.0) -> HazardCurve:
    """Flat hazard that reprices one par spread; used for rating proxies (D-11)."""
    return bootstrap_cds([tenor], [spread], recovery, zero)
