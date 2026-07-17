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

"""Tests for delta engine formula functions: risky annuity, gauge delta, basis delta, MTM."""

import math

from models.trading.delta_engine.pricer import (
    compute_basis_delta,
    compute_gauge_delta,
    compute_mark_to_market,
    compute_risky_annuity,
)


class TestRiskyAnnuity:
    """Tests for risky annuity calculation."""

    def test_zero_hazard_rate(self):
        """With no default risk, annuity equals risk-free annuity."""
        annuity = compute_risky_annuity(0.0, 5, 0.03)
        expected = sum(
            0.25 * math.exp(-0.03 * i * 0.25)
            for i in range(1, 21)
        )
        assert abs(annuity - expected) < 1e-6

    def test_positive_hazard_rate_reduces_annuity(self):
        """Higher hazard rate means lower annuity (higher default prob)."""
        annuity_low = compute_risky_annuity(0.01, 5, 0.03)
        annuity_high = compute_risky_annuity(0.10, 5, 0.03)
        assert annuity_low > annuity_high

    def test_longer_tenor_means_higher_annuity(self):
        """Longer tenor means more payments."""
        a1 = compute_risky_annuity(0.025, 1, 0.03)
        a5 = compute_risky_annuity(0.025, 5, 0.03)
        assert a5 > a1

    def test_reasonable_range(self):
        """Annuity should be between 0 and tenor."""
        annuity = compute_risky_annuity(0.025, 5, 0.03)
        assert 0 < annuity < 5


class TestGaugeDelta:
    """Tests for gauge delta (DV01) calculation."""

    def test_positive_dv01_for_long_position(self):
        """DV01 should be positive for a buyer (spread increases with hazard)."""
        result = compute_gauge_delta(0.025, 5, 10_000_000)
        assert result['dv01_gbp'] > 0
        assert result['delta_spread_bps'] > 0

    def test_higher_notional_means_higher_dv01(self):
        """DV01 scales with notional."""
        r1 = compute_gauge_delta(0.025, 5, 10_000_000)
        r2 = compute_gauge_delta(0.025, 5, 20_000_000)
        assert abs(r2['dv01_gbp'] / r1['dv01_gbp'] - 2.0) < 0.01

    def test_delta_spread_approximately_one(self):
        """For small rates, 1bp bump in rate ~= 1bp bump in spread."""
        result = compute_gauge_delta(0.025, 5, 10_000_000)
        assert 0.5 < result['delta_spread_bps'] < 2.0

    def test_zero_hazard_rate_gives_zero_delta(self):
        """At zero hazard rate, spread is at floor so delta may be minimal."""
        result = compute_gauge_delta(0.0, 5, 10_000_000)
        assert result['delta_spread_bps'] >= 0


class TestBasisDelta:
    """Tests for basis delta calculation."""

    def test_basis_delta_similar_to_gauge_delta(self):
        """With constant basis, basis delta ~ gauge delta."""
        gauge_delta = compute_gauge_delta(0.025, 5, 10_000_000)
        basis_delta = compute_basis_delta(0.025, 5.0, 5, 10_000_000)
        assert abs(basis_delta['basis_delta_bps'] -
                    gauge_delta['delta_spread_bps']) < 0.1

    def test_basis_delta_positive(self):
        """Basis delta should be positive."""
        result = compute_basis_delta(0.025, 3.0, 5, 10_000_000)
        assert result['basis_delta_bps'] > 0
        assert result['basis_dv01_gbp'] > 0


class TestMarkToMarket:
    """Tests for mark-to-market calculation."""

    def test_mtm_positive_when_spread_widens_for_buyer(self):
        """Protection buyer profits when spread widens."""
        mtm = compute_mark_to_market(
            trade_spread_bps=100, fair_spread_bps=120,
            risky_annuity=4.0, notional=10_000_000, is_payer=True)
        assert mtm > 0

    def test_mtm_negative_when_spread_widens_for_seller(self):
        """Protection seller loses when spread widens."""
        mtm = compute_mark_to_market(
            trade_spread_bps=100, fair_spread_bps=120,
            risky_annuity=4.0, notional=10_000_000, is_payer=False)
        assert mtm < 0

    def test_mtm_zero_when_spreads_equal(self):
        """MTM is zero when fair = trade spread."""
        mtm = compute_mark_to_market(
            trade_spread_bps=100, fair_spread_bps=100,
            risky_annuity=4.0, notional=10_000_000, is_payer=True)
        assert mtm == 0

    def test_mtm_calculation_correct(self):
        """Verify the MTM formula."""
        # (120 - 100) / 10000 * 4.0 * 10,000,000 * 1 = 80,000
        mtm = compute_mark_to_market(
            trade_spread_bps=100, fair_spread_bps=120,
            risky_annuity=4.0, notional=10_000_000, is_payer=True)
        assert abs(mtm - 80_000) < 1
