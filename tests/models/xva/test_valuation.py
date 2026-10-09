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

"""Risk-free value: at t = 0 it is the PRS pricer's, and through time it
behaves as the contract says (saw-tooth at premium dates, zero at maturity)."""

import math

import numpy as np
import pytest

from config.port import DEFAULT_YIELD_CURVE
from models.hazard.prs_analytical import compute_prs_spread
from models.trading.delta_engine.pricer import compute_mark_to_market, compute_risky_annuity
from models.xva.valuation import fair_spread, legs, pending_payout, premium_dates, value

from ._fixtures import HUMPED, NOTIONAL, case


class TestReproducesThePricer:

    @pytest.mark.parametrize("p", [0.005, 0.02, 0.08])
    @pytest.mark.parametrize("tenor", [1, 2, 3, 5])
    def test_fair_spread_and_annuity(self, p, tenor):
        trade, market, _, _ = case(curve=HUMPED, tenor=tenor,
                                   lam_e=-math.log(1 - p))
        expected = compute_prs_spread(p, tenor, 0.0, yield_curve=DEFAULT_YIELD_CURVE)
        assert fair_spread(trade, market.zero) * 1e4 == pytest.approx(expected, rel=1e-12)
        assert legs(trade, market.zero, 0.0)["annuity"] == pytest.approx(
            compute_risky_annuity(p, tenor, yield_curve=DEFAULT_YIELD_CURVE), rel=1e-12)

    @pytest.mark.parametrize("buyer", [True, False])
    def test_value_is_the_trading_desk_mtm(self, buyer):
        trade, market, _, _ = case(curve=HUMPED, buyer=buyer, spread=0.0150)
        fair_bps = compute_prs_spread(0.02, 5, 0.0, yield_curve=DEFAULT_YIELD_CURVE)
        annuity = compute_risky_annuity(0.02, 5, yield_curve=DEFAULT_YIELD_CURVE)
        mtm = compute_mark_to_market(150.0, fair_bps, annuity, NOTIONAL, is_payer=buyer)
        assert value(trade, market.zero, 0.0) == pytest.approx(mtm, abs=0.01)  # pricer rounds to 1p

    def test_value_is_zero_at_the_fair_spread(self):
        trade, market, _, _ = case(curve=HUMPED)
        from dataclasses import replace
        at_par = replace(trade, spread=fair_spread(trade, market.zero))
        assert abs(value(at_par, market.zero, 0.0)) < 1e-6


class TestThroughTime:

    def test_matches_the_reference_cash_flows(self):
        trade, market, _, ref = case(curve=HUMPED, buyer=False)
        for t in np.linspace(0.0, 5.2, 105):
            assert value(trade, market.zero, t) == pytest.approx(ref.v(t), rel=1e-12, abs=1e-6)

    def test_jumps_by_the_premium_at_each_payment_date(self):
        trade, market, _, _ = case()
        for t_i in premium_dates(trade)[:-1]:
            before = value(trade, market.zero, t_i - 1e-10)
            after = value(trade, market.zero, t_i)
            assert after - before == pytest.approx(trade.spread * 0.25 * NOTIONAL, rel=1e-6)

    def test_is_continuous_inside_a_period(self):
        trade, market, _, _ = case(curve=HUMPED)
        for t in (0.1, 1.3, 2.6, 4.9):
            assert value(trade, market.zero, t + 1e-9) == pytest.approx(
                value(trade, market.zero, t), abs=1e-2)

    def test_is_zero_at_and_after_maturity(self):
        trade, market, _, _ = case()
        assert value(trade, market.zero, 5.0) == 0.0
        assert value(trade, market.zero, 6.0) == 0.0

    def test_seller_is_the_mirror_of_the_buyer(self):
        buy, market, _, _ = case(buyer=True)
        sell, _, _, _ = case(buyer=False)
        for t in (0.0, 0.7, 3.3):
            assert value(sell, market.zero, t) == -value(buy, market.zero, t)

    def test_pending_payout_discounts_to_settlement(self):
        trade, market, _, _ = case()
        got = pending_payout(trade, market.zero, 1.0, 1.0, 0.02)
        assert got == pytest.approx(NOTIONAL * math.exp(-0.03 * 0.02), rel=1e-12)
