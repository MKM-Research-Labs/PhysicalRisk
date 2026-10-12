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

"""The CIR++ hazard factor (D-15): closed forms against simulation, the exact
fit to the market curve, and the deterministic limit that is WP1."""

import math

import numpy as np
import pytest

from models.xva import HazardCurve
from models.xva.cir import CirFactor, ShiftedTrigger

LAMBDA = -math.log(0.98)


def _simulate_integral(factor, horizon, n_paths=100_000, steps=500, seed=7):
    rng = np.random.default_rng(seed)
    dt = horizon / steps
    y, integral = np.ones(n_paths), np.zeros(n_paths)
    for _ in range(steps):
        nxt = factor.step(y, dt, rng)
        integral += 0.5 * (y + nxt) * dt
        y = nxt
    return y, integral


class TestFactor:

    def test_bond_price_matches_simulation(self):
        factor = CirFactor(0.5, 0.6)
        _, integral = _simulate_integral(factor, 5.0)
        sample = np.exp(-3.0 * LAMBDA * integral)
        se = sample.std() / math.sqrt(sample.size)
        assert abs(sample.mean() - factor.survival(5.0, 3.0 * LAMBDA)) < 4 * se

    def test_exact_step_has_the_cir_moments(self):
        factor = CirFactor(0.8, 0.5)
        y, _ = _simulate_integral(factor, 2.0, steps=4)
        var = 0.25 * (1 - math.exp(-1.6)) ** 2 / (2 * 0.8) + 0.25 * math.exp(-0.8 * 2.0)             * (1 - math.exp(-0.8 * 2.0)) / 0.8
        assert y.mean() == pytest.approx(1.0, abs=4 * math.sqrt(var / y.size))
        assert y.var() == pytest.approx(var, rel=0.03)

    def test_zero_vol_is_deterministic_mean_reversion(self):
        factor = CirFactor(0.5, 0.0)
        assert np.allclose(factor.step(np.array([2.0]), 1.0, None), 1 + math.exp(-0.5))
        assert factor.survival(3.0, LAMBDA) == pytest.approx(math.exp(-LAMBDA * 3.0), rel=1e-14)

    def test_small_vol_tends_to_the_deterministic_bond(self):
        a0, b0 = CirFactor(0.5, 0.0).bond(4.0, LAMBDA)
        a1, b1 = CirFactor(0.5, 1e-6).bond(4.0, LAMBDA)
        assert a1 == pytest.approx(a0, rel=1e-9) and b1 == pytest.approx(b0, rel=1e-9)

    def test_zero_step_is_a_copy(self):
        y = np.array([1.3])
        assert CirFactor(0.5, 0.3).step(y, 0.0, None) is not y

    @pytest.mark.parametrize("kappa, sigma", [(0.0, 0.3), (0.5, -0.1)])
    def test_rejects_bad_parameters(self, kappa, sigma):
        with pytest.raises(ValueError):
            CirFactor(kappa, sigma)


class TestShiftedTrigger:

    @pytest.mark.parametrize("sigma", [0.0, 0.3, 0.8])
    def test_reprices_the_market_curve_at_time_zero(self, sigma):
        trig = ShiftedTrigger(CirFactor(0.5, sigma), HazardCurve.flat(LAMBDA))
        t = np.linspace(0.0, 10.0, 41)
        assert np.allclose(trig.survival(0.0, t, 1.0), np.exp(-LAMBDA * t), rtol=1e-13)

    def test_shift_is_a_non_negative_intensity(self):
        trig = ShiftedTrigger(CirFactor(0.5, 0.8), HazardCurve.flat(LAMBDA))
        assert np.all(np.diff(trig.shift_integral(np.linspace(0.0, 10.0, 101))) >= 0)

    def test_higher_hazard_state_lowers_survival(self):
        trig = ShiftedTrigger(CirFactor(0.5, 0.3), HazardCurve.flat(LAMBDA))
        low, high = trig.survival(1.0, np.array([3.0]), np.array([0.5, 2.0]))[:, 0]
        assert high < low


class TestTermStructure:
    """Plan §16: the shift carries a hazard term structure; the stochastic part
    scales with the curve's lowest hazard so the shift stays an intensity."""

    CURVE = HazardCurve([1.0, 3.0, 5.0], [0.012, 0.020, 0.016])

    @pytest.mark.parametrize("sigma", [0.0, 0.3, 0.8])
    def test_reprices_a_term_structure_exactly(self, sigma):
        trig = ShiftedTrigger(CirFactor(0.5, sigma), self.CURVE)
        t = np.linspace(0.0, 8.0, 65)
        assert np.allclose(trig.survival(0.0, t, 1.0), self.CURVE.survival(t), rtol=1e-13)

    def test_scale_is_the_lowest_hazard(self):
        assert ShiftedTrigger(CirFactor(0.5, 0.3), self.CURVE).scale == 0.012

    @pytest.mark.parametrize("sigma", [0.0, 0.3, 0.8])
    def test_shift_is_a_non_negative_intensity(self, sigma):
        phi = ShiftedTrigger(CirFactor(0.5, sigma), self.CURVE).shift_integral(
            np.linspace(0.0, 8.0, 161))
        assert phi[0] == 0.0 and np.all(np.diff(phi) >= -1e-15)

    def test_flat_curve_has_no_shift_without_volatility(self):
        trig = ShiftedTrigger(CirFactor(0.5, 0.0), HazardCurve.flat(LAMBDA))
        assert np.allclose(trig.shift_integral(np.linspace(0, 5, 11)), 0.0, atol=1e-15)
