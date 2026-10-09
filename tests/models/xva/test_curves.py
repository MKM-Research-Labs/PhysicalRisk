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

"""Curves: the zero curve reproduces the pricer's discounting, hazard curves
integrate correctly, and the CDS bootstrap reprices its inputs."""

import math

import numpy as np
import pytest
from scipy.integrate import quad

from config.port import DEFAULT_YIELD_CURVE
from models.hazard.prs_analytical import compute_prs_spread, interpolate_yield_rate
from models.xva import HazardCurve, ZeroCurve, bootstrap_cds, cds_par_spread, flat_cds_curve

TIMES = np.linspace(0.0, 8.0, 161)


class TestZeroCurve:

    @pytest.mark.parametrize("curve", [DEFAULT_YIELD_CURVE, None])
    def test_discount_factor_is_the_pricers(self, curve):
        zero = ZeroCurve(curve, 0.03)
        for t in TIMES:
            r = interpolate_yield_rate(curve, t, 0.03) if curve else 0.03
            assert zero.df(t) == pytest.approx(math.exp(-r * t), rel=1e-15)
            assert zero.pricer_rate(t) == pytest.approx(r, rel=1e-15)

    def test_forward_rate_is_the_log_derivative(self):
        zero = ZeroCurve(DEFAULT_YIELD_CURVE)
        for t in (0.3, 1.5, 3.7, 4.2, 5.5, 7.0):
            h = 1e-6
            numeric = -(math.log(zero.df(t + h)) - math.log(zero.df(t - h))) / (2 * h)
            assert zero.forward_rate(t) == pytest.approx(numeric, rel=1e-7)

    def test_flat_curve_has_flat_forward(self):
        assert np.allclose(ZeroCurve(None, 0.025).forward_rate(TIMES), 0.025)


class TestHazardCurve:

    def test_survival_matches_integrated_hazard(self):
        curve = HazardCurve([1.0, 3.0, 5.0], [0.01, 0.03, 0.02])
        for t in (0.5, 1.0, 2.0, 4.0, 7.0):
            integral = quad(lambda u: float(curve.hazard(u)), 0, t, points=[1, 3, 5])[0]
            assert curve.survival(t) == pytest.approx(math.exp(-integral), rel=1e-12)

    def test_last_rate_extends_flat(self):
        curve = HazardCurve([1.0, 2.0], [0.01, 0.05])
        assert curve.hazard(10.0) == 0.05
        assert curve.hazard(1.0) == 0.01        # a knot belongs to its left segment

    def test_annual_probability_conversion_is_the_pricers(self):
        assert HazardCurve.from_annual_probability(0.02).rates[0] == -math.log(0.98)
        assert HazardCurve.from_annual_probability(0.0).rates[0] == 0.0
        assert HazardCurve.from_annual_probability(1.0).rates[0] == pytest.approx(-math.log(0.001))

    @pytest.mark.parametrize("knots, rates", [([], []), ([1, 1], [0.1, 0.1]),
                                              ([0, 1], [0.1, 0.1]), ([1], [-0.1])])
    def test_rejects_malformed_curves(self, knots, rates):
        with pytest.raises(ValueError):
            HazardCurve(knots, rates)


class TestBootstrap:

    def test_par_spread_matches_the_prs_pricer(self):
        """The CDS convention is the pricer's, so a flat flood hazard reprices."""
        zero = ZeroCurve(DEFAULT_YIELD_CURVE)
        for p in (0.005, 0.02, 0.10):
            par = cds_par_spread(HazardCurve.from_annual_probability(p), zero, 5, 0.0)
            assert par * 1e4 == pytest.approx(
                compute_prs_spread(p, 5, 0.0, yield_curve=DEFAULT_YIELD_CURVE), rel=1e-12)

    def test_reprices_every_input(self):
        zero = ZeroCurve(DEFAULT_YIELD_CURVE)
        tenors, spreads = [1, 3, 5, 7], [0.0080, 0.0110, 0.0140, 0.0150]
        curve = bootstrap_cds(tenors, spreads, 0.4, zero)
        for tenor, spread in zip(tenors, spreads):
            assert cds_par_spread(curve, zero, tenor, 0.4) == pytest.approx(spread, abs=1e-13)
        assert np.all(curve.rates > 0)

    def test_flat_curve_is_close_to_the_credit_triangle(self):
        curve = flat_cds_curve(0.0120, 0.4, ZeroCurve(DEFAULT_YIELD_CURVE))
        assert curve.rates[0] == pytest.approx(0.0120 / 0.6, rel=0.01)

    def test_distressed_spread_needs_a_hazard_above_one(self):
        zero = ZeroCurve()
        curve = flat_cds_curve(1.0, 0.4, zero)
        assert curve.rates[0] > 1.0
        assert cds_par_spread(curve, zero, 5.0, 0.4) == pytest.approx(1.0, abs=1e-12)

    def test_rejects_inadmissible_and_unsorted_inputs(self):
        zero = ZeroCurve()
        with pytest.raises(ValueError, match="minimum admissible"):
            bootstrap_cds([1, 2], [0.0200, 0.0010], 0.4, zero)
        with pytest.raises(ValueError, match="increasing"):
            bootstrap_cds([2, 1], [0.01, 0.01], 0.4, zero)
