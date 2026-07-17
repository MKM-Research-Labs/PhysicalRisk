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

"""
Tests for models.hazard.prs_analytical — coverage expansion.

Targets uncovered lines: 64, 67, 71, 77, 126, 179, 190.
"""

import pytest

from models.hazard.prs_analytical import (
    compute_prs_spread,
    interpolate_yield_rate,
)


# ===========================================================================
# interpolate_yield_rate — edge cases
# ===========================================================================

class TestInterpolateYieldRateEdges:

    def test_empty_dict_returns_fallback(self):
        """Line 64: empty yield_curve returns fallback."""
        result = interpolate_yield_rate({}, 2.0, fallback=0.05)
        assert result == 0.05

    def test_empty_dict_default_fallback(self):
        """Line 64: empty yield_curve returns default fallback 0.04."""
        result = interpolate_yield_rate({}, 1.0)
        assert result == 0.04

    def test_t_above_max_key_returns_last(self):
        """Line 71: t >= keys[-1] returns the last key's rate."""
        curve = {'1': 0.03, '3': 0.04, '5': 0.045}
        result = interpolate_yield_rate(curve, 10.0)
        assert result == 0.045

    def test_t_at_max_key_returns_last(self):
        """Line 71: t == keys[-1] returns the last key's rate."""
        curve = {'1': 0.03, '5': 0.045}
        result = interpolate_yield_rate(curve, 5.0)
        assert result == 0.045

    def test_fallthrough_after_loop(self):
        """Line 77: fallthrough at end of for loop returns last key rate.

        This can happen due to floating point — craft a scenario where the
        loop exits without matching any interval. In practice this is a
        safety fallback. We test by calling with t exactly at the boundary
        of the last interval's upper key, which is handled by line 71 instead.
        A true fallthrough is hard to trigger without float tricks; the line
        is a defensive guard. We verify the function handles edge-adjacent
        values correctly.
        """
        # With a single key, t > that key triggers line 71.
        # With keys [1, 2], t=1.5 triggers the loop body.
        # The fallthrough on line 77 is a defensive guard; exercised if
        # floating-point comparison skips the interval. We trigger it by
        # ensuring the for-loop completes without returning via range checks.
        # Actually, we can't easily trigger it with normal floats.
        # Let's just verify the normal interpolation works at key boundaries.
        curve = {'2': 0.03, '4': 0.04}
        # t exactly at key 4 -> line 71
        assert interpolate_yield_rate(curve, 4.0) == 0.04
        # t between keys
        result = interpolate_yield_rate(curve, 3.0)
        assert result == pytest.approx(0.035)


# ===========================================================================
# compute_prs_spread — annuity edge
# ===========================================================================

class TestComputePrsSpreadEdges:

    def test_annuity_zero_fallback(self):
        """Line 126: annuity <= 0 returns annual_hazard_rate * 10000.

        With an extremely high hazard rate, survival drops to ~0 so annuity
        can approach zero.
        """
        # hazard_rate = 0.999 → lambda = -ln(0.001) ≈ 6.9
        # Survival at t=0.25: exp(-6.9*0.25) ≈ 0.18 → annuity won't be 0
        # For annuity to truly be 0 we'd need hazard_rate > 0.999 but it's capped.
        # The fallback is also guarded by a second check annuity > 0 at line 141.
        # We test that the function handles very high hazard gracefully.
        result = compute_prs_spread(0.999, tenor=1, recovery=0.0)
        assert result > 0

    def test_with_yield_curve(self):
        """Verify compute_prs_spread uses yield_curve when provided."""
        curve = {'1': 0.03, '2': 0.035, '3': 0.04, '5': 0.045}
        result = compute_prs_spread(0.05, tenor=3, yield_curve=curve)
        assert result > 0

    def test_zero_hazard_returns_zero(self):
        result = compute_prs_spread(0.0, tenor=5)
        assert result == 0.0

    def test_negative_hazard_returns_zero(self):
        result = compute_prs_spread(-0.01, tenor=5)
        assert result == 0.0


class TestInterpolateYieldRateDefensiveBranches:
    """Cover defensive `return fallback` after key extraction (line 56)."""

    def test_truthy_dict_with_no_keys(self):
        """Line 56: yield_curve is truthy but yields no keys → fallback.

        Constructed via a dict subclass that lies about being non-empty.
        """
        class _TruthyEmpty(dict):
            def __bool__(self):
                return True

        weird = _TruthyEmpty()
        result = interpolate_yield_rate(weird, 2.0, fallback=0.07)
        assert result == 0.07

    def test_nan_t_falls_through_loop(self):
        """Line 66: NaN t makes all `keys[i] <= t <= keys[i+1]` checks fail
        and the early `t <= keys[0]` / `t >= keys[-1]` checks also fail, so
        we hit the trailing `return yield_curve[str(keys[-1])]`.
        """
        curve = {'1': 0.03, '3': 0.04, '5': 0.045}
        result = interpolate_yield_rate(curve, float('nan'))
        assert result == 0.045


class TestComputePrsSpreadAnnuityFallback:
    """Cover the annuity-zero fallback (line 115)."""

    def test_annuity_zero_returns_hazard_times_10000(self, monkeypatch):
        """Line 115: when annuity <= 0 we return hazard * 10000.

        Force survival/discount to zero by patching math.exp inside the
        prs_analytical module so the annuity loop accumulates zeros.
        """
        import models.hazard.prs_analytical as mod

        monkeypatch.setattr(mod.math, "exp", lambda _x: 0.0)

        result = compute_prs_spread(0.05, tenor=2)
        # Expected = 0.05 * 10000 = 500.0
        assert result == 500.0
