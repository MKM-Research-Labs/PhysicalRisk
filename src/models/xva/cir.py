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

"""Stochastic flood-trigger intensity: shifted CIR (CIR++), D-15.

A catchment hazard factor Y follows CIR with Y(0) = theta = 1,

    dY = kappa (1 - Y) dt + sigma sqrt(Y) dW,

so E[Y(t)] = 1: the factor moves the market's view of hazard without biasing
it. Gauge g's trigger intensity is lambda_g Y(t) + phi_g(t). The shift phi_g
is fitted so the model's survival at t = 0 is exactly the market curve the
pricer uses (Brigo-Mercurio CIR++; Green's intensity family, 16.352), so V(0)
on every path still reproduces MKM-PR-001. With sigma = 0 the shift is zero
and the model is the deterministic WP1 engine exactly.

Given Y(t) = y and no trigger by t, survival to u is

    S(t, u) = exp(-(Phi_g(u) - Phi_g(t))) A(u - t) exp(-B(u - t) lambda_g y)

with A, B the CIR bond-price functions for X = lambda_g Y (kappa, theta =
lambda_g, sigma sqrt(lambda_g)), and Phi_g the integrated shift.
"""

import numpy as np

from .curves import HazardCurve


class CirFactor:
    """The catchment factor Y and its closed forms for a scaled copy lambda Y."""

    def __init__(self, kappa: float, sigma: float):
        if kappa <= 0 or sigma < 0:
            raise ValueError("kappa must be positive and sigma non-negative")
        self.kappa, self.sigma = kappa, sigma

    def bond(self, tau, scale: float):
        """(A, B) for X = scale * Y over horizon tau: E[exp(-int X)] = A exp(-B X0)."""
        tau = np.asarray(tau, dtype=float)
        k, theta, s2 = self.kappa, scale, self.sigma ** 2 * scale
        if s2 == 0.0:
            b = (1.0 - np.exp(-k * tau)) / k
            return np.exp(-theta * (tau - b)), b
        g = np.sqrt(k * k + 2.0 * s2)
        e = np.expm1(g * tau)
        b = 2.0 * e / ((g + k) * e + 2.0 * g)
        # The textbook ln A = (2 k theta / s2) [ln 2g + (k+g) tau / 2 - ln den]
        # multiplies a huge factor by a vanishing difference as s2 -> 0. With
        # x = g - k = 2 s2 / (g + k), the bracket is -[x tau / 2 + log1p(-x (1 -
        # exp(-g tau)) / 2g)]: both terms O(s2), computed without cancellation.
        x = 2.0 * s2 / (g + k)
        log_d = 0.5 * x * tau + np.log1p(-x * -np.expm1(-g * tau) / (2.0 * g))
        return np.exp(-(2.0 * k * theta / s2) * log_d), b

    def survival(self, tau, scale: float, y0=1.0):
        a, b = self.bond(tau, scale)
        return a * np.exp(-b * scale * np.asarray(y0))

    def step(self, y: np.ndarray, dt: float, rng: np.random.Generator) -> np.ndarray:
        """Exact transition Y(t) -> Y(t + dt): a scaled noncentral chi-square."""
        if dt <= 0:
            return y.copy()
        k, s = self.kappa, self.sigma
        if s == 0.0:
            return 1.0 + (y - 1.0) * np.exp(-k * dt)
        c = s * s * (1.0 - np.exp(-k * dt)) / (4.0 * k)
        df = 4.0 * k / (s * s)
        nonc = y * np.exp(-k * dt) / c
        return c * rng.noncentral_chisquare(df, nonc)


class ShiftedTrigger:
    """One gauge's CIR++ trigger intensity, fitted to its market hazard curve."""

    def __init__(self, factor: CirFactor, market: HazardCurve):
        self.factor, self.market = factor, market
        self.scale = float(market.hazard(0.0))
        if np.any(market.rates != self.scale) and factor.sigma > 0:
            raise ValueError("CIR++ fit is implemented for a flat trigger hazard (the pricer's)")

    def shift_integral(self, t):
        """Phi(t) = H_market(t) + ln P_CIR(0, t): the deterministic part's integral."""
        t = np.asarray(t, dtype=float)
        if self.factor.sigma == 0.0:
            return np.zeros_like(t)
        return self.market.integrated(t) + np.log(self.factor.survival(t, self.scale))

    def survival(self, t, u, y):
        """S(t, u) given Y(t) = y and no trigger by t; broadcasts over y and u."""
        t = float(t)
        u = np.asarray(u, dtype=float)
        tau = u - t
        shift = np.exp(-(self.shift_integral(u) - self.shift_integral(t)))
        a, b = self.factor.bond(tau, self.scale)
        return shift * a * np.exp(-np.multiply.outer(np.asarray(y), b * self.scale))
