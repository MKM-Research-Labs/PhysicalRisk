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

"""An independent re-implementation of the analytic XVA, for benchmarking.

Shares no code with ``models.xva``: plain-Python cash-flow loops, flat
hazards written out by hand, the pricer's own ``interpolate_yield_rate`` for
discounting, and scipy's adaptive ``quad`` for every integral (the engine
uses fixed Gauss-Legendre on precomputed pieces). Slow and simple on purpose:
it is the second implementation Green recommends a validator keep.
"""

import math

from scipy.integrate import quad

from models.hazard.prs_analytical import interpolate_yield_rate

DT = 0.25


class Ref:
    def __init__(self, *, notional, spread, tenor, buyer, lam_e, lam_c, lam_b,
                 rec_c, rec_b, s_f, lag, curve=None, flat_rate=0.03):
        self.n, self.s, self.T = notional, spread, tenor
        self.w = 1.0 if buyer else -1.0
        self.lam_e, self.lam_c, self.lam_b = lam_e, lam_c, lam_b
        self.rec_c, self.rec_b, self.s_f, self.lag = rec_c, rec_b, s_f, lag
        self.curve, self.flat = curve, flat_rate

    def df(self, t):
        r = interpolate_yield_rate(self.curve, t, self.flat) if self.curve else self.flat
        return math.exp(-r * t)

    def v(self, t):
        """Value given no trigger by t, period by period."""
        total = 0.0
        for i in range(1, int(round(self.T / DT)) + 1):
            end = i * DT
            if end <= t:
                continue
            start = max(end - DT, t)
            q_start = math.exp(-self.lam_e * (start - t))
            q_end = math.exp(-self.lam_e * (end - t))
            prot = (q_start - q_end) * self.df(0.5 * (start + end)) / self.df(t)
            prem = self.s * DT * q_end * self.df(end) / self.df(t)
            total += prot - prem
        return self.w * self.n * total

    def pending(self, s):
        lo, hi = max(0.0, s - self.lag), min(s, self.T)
        if self.lag == 0 or hi <= lo:
            return 0.0
        f = lambda u: (self.lam_e * math.exp(-self.lam_e * u)
                       * self.w * self.n * self.df(u + self.lag) / self.df(s))
        return quad(f, lo, hi, epsabs=0, epsrel=1e-13, limit=200)[0]

    def exposure(self, s, kind):
        pre = self.v(s) * math.exp(-self.lam_e * s) if s < self.T else 0.0
        post = self.pending(s)
        if kind == "epe":
            return max(pre, 0.0) + max(post, 0.0)
        if kind == "ene":
            return min(pre, 0.0) + min(post, 0.0)
        return pre + post

    def _integral(self, rate, kind, extra_hazard):
        def f(s):
            disc = self.df(s) * math.exp(-(self.lam_c + extra_hazard) * s)
            return rate * disc * self.exposure(s, kind)
        horizon = self.T + self.lag
        points = sorted({i * DT for i in range(1, int(round(self.T / DT)) + 1)}
                        | {float(k) for k in range(1, 7)} | {self.lag, self.T})
        points = [p for p in points if 0 < p < horizon]
        return -quad(f, 0.0, horizon, points=points, epsabs=1e-7, epsrel=1e-11, limit=2000)[0]

    def one_bond(self):
        cva = self._integral((1 - self.rec_c) * self.lam_c, "epe", self.s_f)
        fva = self._integral(self.s_f, "ee", self.s_f)
        return {"cva": cva, "fva": fva}

    def semi_replication(self):
        return {
            "cva": self._integral((1 - self.rec_c) * self.lam_c, "epe", self.lam_b),
            "dva": self._integral((1 - self.rec_b) * self.lam_b, "ene", self.lam_b),
            "fca": self._integral((1 - self.rec_b) * self.lam_b, "epe", self.lam_b),
        }
