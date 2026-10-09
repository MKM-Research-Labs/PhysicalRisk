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

"""Limiting cases from the validation plan (§6): each adjustment vanishes, or
two adjustments coincide, exactly where the theory says they must."""

from dataclasses import replace

import pytest

from models.xva import HazardCurve, analytic

from ._fixtures import HUMPED, case


def _xva(**kw):
    trade, market, cfg, _ = case(**kw)
    return analytic.xva(trade, market, cfg)


@pytest.mark.parametrize("buyer", [True, False])
def test_no_counterparty_default_means_no_cva(buyer):
    views = _xva(buyer=buyer, lam_c=0.0)
    assert views["one_bond"]["cva"] == 0.0
    assert views["semi_replication"]["cva"] == 0.0


def test_full_recovery_means_no_cva():
    views = _xva(counterparty_recovery=1.0)
    assert views["one_bond"]["cva"] == 0.0


def test_no_funding_spread_means_no_fva_dva_or_fca():
    views = _xva(own_funding_spread=0.0)
    assert views["one_bond"]["fva"] == 0.0
    assert views["semi_replication"]["dva"] == 0.0
    assert views["semi_replication"]["fca"] == 0.0


def test_offsetting_trades_have_no_net_funding_adjustment():
    """A payer and a receiver on the same terms: E[V] cancels, so FVA does."""
    buy, sell = _xva(buyer=True, curve=HUMPED), _xva(buyer=False, curve=HUMPED)
    assert buy["one_bond"]["fva"] + sell["one_bond"]["fva"] == pytest.approx(0.0, abs=1e-9)


def test_zero_recovery_funding_makes_the_two_views_identical():
    """With R_B = 0, s_F = lambda_B: the kernels coincide and DVA + FCA is
    exactly the symmetric FVA (Green 9.58-9.59 against 9.64-9.67)."""
    views = _xva(curve=HUMPED, own_recovery=0.0)
    ob, sr = views["one_bond"], views["semi_replication"]
    assert sr["cva"] == pytest.approx(ob["cva"], rel=1e-13)
    assert sr["dva"] + sr["fca"] == pytest.approx(ob["fva"], rel=1e-13)
    assert sr["total"] == pytest.approx(ob["total"], rel=1e-13)


def test_buyer_cva_is_seller_dva_with_the_roles_swapped():
    """Swap the bank and the counterparty: one side's CVA is the other's DVA."""
    lam = 0.03
    buy, market, cfg, _ = case(buyer=True, curve=HUMPED, lam_c=lam,
                               own_funding_spread=lam * 0.6, own_recovery=0.4)
    sell = replace(buy, bank_buys_protection=False)
    cva = analytic.xva(buy, market, cfg)["semi_replication"]["cva"]
    dva = analytic.xva(sell, market, cfg)["semi_replication"]["dva"]
    assert cva == pytest.approx(-dva, rel=1e-13)


def test_no_settlement_lag_leaves_only_the_pre_trigger_exposure():
    """Under independence the jump to notional costs nothing without a lag."""
    views = _xva(spread=0.0300, settlement_days=0)   # buyer out of the money: EPE = 0
    assert views["one_bond"]["cva"] == 0.0


def test_no_flood_hazard_leaves_the_buyer_owing_premium_only():
    """With no trigger the buyer's value is minus the premiums: never positive."""
    trade, market, cfg, _ = case(lam_e=0.0)
    assert analytic.xva(trade, market, cfg)["one_bond"]["cva"] == 0.0


def test_cva_grows_with_counterparty_hazard():
    low = _xva(buyer=False, lam_c=0.01)["one_bond"]["cva"]
    high = _xva(buyer=False, lam_c=0.05)["one_bond"]["cva"]
    assert high < low < 0.0


def test_settlement_lag_drives_the_buyers_jump_cva():
    """At the fair spread the buyer's CVA is almost all jump term, roughly
    (1 - R_C) N lambda_C lag x P(trigger before T) (plan §3.4)."""
    trade, market, cfg, _ = case(spread=0.0204)
    short = analytic.xva(trade, market, replace(cfg, settlement_days=5))["one_bond"]["cva"]
    long = analytic.xva(trade, market, replace(cfg, settlement_days=20))["one_bond"]["cva"]
    assert long / short == pytest.approx(4.0, rel=0.15)


def test_survival_discounting_lowers_every_adjustment():
    """D-03: weaker names are discounted harder, so a riskier bank pays less KVA-like cost."""
    trade, market, cfg, _ = case(buyer=False)
    base = analytic.xva(trade, market, cfg)["semi_replication"]["cva"]
    weak = replace(market, own=HazardCurve.flat(0.20))
    assert abs(analytic.xva(trade, weak, cfg)["semi_replication"]["cva"]) < abs(base)
