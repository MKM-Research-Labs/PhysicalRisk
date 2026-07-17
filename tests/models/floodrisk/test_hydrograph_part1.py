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

"""Tests for hydrograph superposition module -- part 1 (unit functions)."""

import math

import numpy as np
import pytest

from models.floodrisk.hydrograph import (
    apply_infiltration,
    build_pulse_gauge_hydrograph,
    compute_saturation_factor,
    gamma_shape,
    gamma_shape_array,
    superimpose_pulses,
)


# ---------------------------------------------------------------------------
# gamma_shape
# ---------------------------------------------------------------------------

class TestGammaShape:

    @pytest.mark.parametrize("alpha", [0.3, 0.5, 0.7, 1.0])
    def test_peak_at_alpha_squared(self, alpha):
        """phi(alpha^2) should equal 1.0 (the normalised peak)."""
        val = gamma_shape(alpha * alpha, alpha)
        assert abs(val - 1.0) < 1e-10

    def test_zero_at_zero(self):
        assert gamma_shape(0.0, 0.3) == 0.0

    def test_zero_beyond_one(self):
        assert gamma_shape(1.01, 0.5) == 0.0

    def test_negative_u(self):
        assert gamma_shape(-0.1, 0.5) == 0.0

    def test_invalid_alpha(self):
        assert gamma_shape(0.5, 0.0) == 0.0
        assert gamma_shape(0.5, -1.0) == 0.0

    @pytest.mark.parametrize("alpha", [0.3, 0.7, 1.0])
    def test_max_is_one(self, alpha):
        """The maximum value over u in (0,1] should be 1.0 at u=alpha."""
        us = np.linspace(0.001, 1.0, 1000)
        vals = [gamma_shape(u, alpha) for u in us]
        assert max(vals) == pytest.approx(1.0, abs=1e-4)

    def test_asymmetric_for_small_alpha(self):
        """alpha=0.3 -> fast rise, long tail."""
        rise_val = gamma_shape(0.15, 0.3)  # halfway to peak
        fall_val = gamma_shape(0.65, 0.3)  # same distance past peak
        # Rise is steeper so midpoint rise > midpoint fall
        assert rise_val > fall_val


class TestGammaShapeArray:

    def test_matches_scalar(self):
        hours = np.arange(168, dtype=float)
        arr = gamma_shape_array(hours, start_hour=20.0, duration_hours=40.0,
                                alpha=0.3)
        # Check a few manually
        for h in [20, 30, 40, 50, 59]:
            u = (h - 20.0) / 40.0
            expected = gamma_shape(u, 0.3) if 0 < u <= 1 else 0.0
            assert arr[h] == pytest.approx(expected, abs=1e-10)

    def test_zero_outside_window(self):
        arr = gamma_shape_array(np.arange(168, dtype=float),
                                start_hour=50.0, duration_hours=30.0,
                                alpha=0.5)
        assert arr[0] == 0.0
        assert arr[49] == 0.0
        assert arr[81] == 0.0  # 50+30+1 -> outside

    def test_zero_duration_returns_zeros(self):
        """Line 68: duration_hours <= 0 → returns zeros."""
        arr = gamma_shape_array(np.arange(168, dtype=float),
                                start_hour=10.0, duration_hours=0.0,
                                alpha=0.3)
        np.testing.assert_allclose(arr, 0.0)

    def test_negative_duration_returns_zeros(self):
        """Line 68: duration_hours < 0 → returns zeros."""
        arr = gamma_shape_array(np.arange(168, dtype=float),
                                start_hour=10.0, duration_hours=-5.0,
                                alpha=0.3)
        np.testing.assert_allclose(arr, 0.0)


# ---------------------------------------------------------------------------
# build_pulse_gauge_hydrograph
# ---------------------------------------------------------------------------

class TestBuildPulseGaugeHydrograph:

    def test_base_level_when_no_exceedance(self):
        arr = build_pulse_gauge_hydrograph(
            base_level=5.0, peak_m=5.0, start_hour=10,
            duration_hours=30, alpha=0.3
        )
        np.testing.assert_allclose(arr, 5.0)

    def test_peak_near_expected_hour(self):
        arr = build_pulse_gauge_hydrograph(
            base_level=3.0, peak_m=8.0, start_hour=20,
            duration_hours=40, alpha=0.3
        )
        peak_hour = int(np.argmax(arr))
        # Peak at u = alpha^2 = 0.09, so hour = 20 + 0.09 * 40 ~ 23.6
        expected = 20 + int(0.3 * 0.3 * 40)
        assert abs(peak_hour - expected) <= 2

    def test_peak_value(self):
        arr = build_pulse_gauge_hydrograph(
            base_level=3.0, peak_m=8.0, start_hour=20,
            duration_hours=40, alpha=0.3
        )
        # Peak should reach close to 8.0 (discretisation may lose a fraction)
        assert max(arr) == pytest.approx(8.0, abs=0.5)


# ---------------------------------------------------------------------------
# compute_saturation_factor
# ---------------------------------------------------------------------------

class TestSaturationFactor:

    def test_identity_no_antecedent(self):
        assert compute_saturation_factor(0.0) == 1.0

    def test_monotonic(self):
        s1 = compute_saturation_factor(50.0)
        s2 = compute_saturation_factor(100.0)
        s3 = compute_saturation_factor(200.0)
        assert 1.0 < s1 < s2 < s3

    def test_known_value(self):
        # s = 1 + 0.2 * log(1 + 100/50) = 1 + 0.2 * log(3) ~ 1.2197
        expected = 1.0 + 0.2 * math.log(3.0)
        assert compute_saturation_factor(100.0) == pytest.approx(expected)

    def test_negative_precip(self):
        assert compute_saturation_factor(-10.0) == 1.0


# ---------------------------------------------------------------------------
# superimpose_pulses
# ---------------------------------------------------------------------------

class TestSuperimposePulses:

    def test_empty_pulses(self):
        result = superimpose_pulses(5.0, [])
        assert len(result) == 168
        np.testing.assert_allclose(result, 5.0)

    def test_single_pulse(self):
        pulse = np.full(168, 5.0)
        pulse[50:60] = 8.0  # 3m exceedance
        result = superimpose_pulses(5.0, [pulse])
        assert result[55] == pytest.approx(8.0)
        assert result[0] == pytest.approx(5.0)

    def test_non_overlapping_sequential(self):
        base = 5.0
        p1 = np.full(168, base)
        p1[20:30] = 7.0  # 2m exceedance
        p2 = np.full(168, base)
        p2[50:60] = 8.0  # 3m exceedance
        result = superimpose_pulses(base, [p1, p2])
        assert result[25] == pytest.approx(7.0)
        assert result[55] == pytest.approx(8.0)
        assert result[0] == pytest.approx(5.0)

    def test_overlapping_exceeds_single(self):
        base = 5.0
        p1 = np.full(168, base)
        p1[40:60] = 7.0
        p2 = np.full(168, base)
        p2[50:70] = 7.0
        result = superimpose_pulses(base, [p1, p2])
        # Overlap zone: both contribute 2m each -> 5 + 4 = 9
        assert result[55] == pytest.approx(9.0)
        # Non-overlap: only one contributes
        assert result[45] == pytest.approx(7.0)

    def test_cap(self):
        base = 5.0
        p1 = np.full(168, base)
        p1[40:60] = 10.0  # 5m exceedance
        p2 = np.full(168, base)
        p2[45:55] = 10.0  # 5m exceedance
        result = superimpose_pulses(base, [p1, p2], cap=6.0)
        # Overlap would be 10m exceedance, capped at 6
        assert result[50] == pytest.approx(11.0)  # base + cap


# ---------------------------------------------------------------------------
# apply_infiltration
# ---------------------------------------------------------------------------

class TestInfiltration:

    def test_reduces_depth(self):
        raw = np.array([0.0] * 50 + [1.0] * 50 + [0.0] * 68)
        result = apply_infiltration(raw, kappa=0.01, y_max=0.2, f_imperv=0.0)
        # Should be <= raw at all hours
        assert np.all(result <= raw + 1e-10)
        # First flooded hour should be reduced
        assert result[50] < raw[50]

    def test_saturates(self):
        """After Y_max is consumed, depth passes through unchanged."""
        raw = np.array([2.0] * 168)
        result = apply_infiltration(raw, kappa=0.5, y_max=0.1, f_imperv=0.0)
        # First hour loses some to infiltration
        assert result[0] < raw[0]
        # After ground saturates (Y_max=0.1, kappa=0.5, first step absorbs
        # min(0.5*2*1, 0.1)=0.1 -> saturated after step 0), rest pass through
        assert result[1] == pytest.approx(raw[1])

    def test_fully_impervious(self):
        """f_imperv=1 -> Y_max=0 -> no infiltration -> depth unchanged."""
        raw = np.array([1.5] * 168)
        result = apply_infiltration(raw, kappa=0.01, y_max=0.2, f_imperv=1.0)
        np.testing.assert_allclose(result, raw)

    def test_zero_depth(self):
        raw = np.zeros(168)
        result = apply_infiltration(raw)
        np.testing.assert_allclose(result, 0.0)
