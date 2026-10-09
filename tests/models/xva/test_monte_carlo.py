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

"""The Monte Carlo engine (WP2).

Exit test first: with sigma = 0, one trade, no collateral and beta = 0 the
engine reproduces the analytic engine within 3 standard errors on every
term (plan §5). Then the properties each new feature must have.
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from config.xva import XvaConfig
from models.xva import HazardCurve, Market, PrsTrade, ZeroCurve, analytic
from models.xva import monte_carlo as mc
from models.xva.cir import CirFactor, ShiftedTrigger
from models.xva.events import TriggerModel
from models.xva.exposure_analytic import profiles
from models.xva.integrals import kernel
from models.xva.netting import Csa, NettingSet
from models.xva.paths import alive_value, grid
from models.xva.valuation import fair_spread, value

from ._fixtures import HUMPED

ZERO = ZeroCurve(HUMPED)
LAM_E = HazardCurve.from_annual_probability(0.02)
LAM_C = HazardCurve.flat(0.02)
FAST = XvaConfig(n_paths=2_000)


def _trade(buyer=True, gauge="G1", spread=None):
    t = PrsTrade(1e7, 0.018, 5, buyer, LAM_E, gauge)
    return replace(t, spread=fair_spread(t, ZERO)) if spread == "fair" else t


def _value(out, view, term):
    return out["views"][view][term]["value"]


class TestReconcilesToTheAnalyticEngine:

    @pytest.mark.parametrize("buyer", [True, False])
    def test_deterministic_single_trade(self, buyer):
        cfg = XvaConfig(hazard_vol=0.0)
        trade = _trade(buyer)
        out = mc.run(NettingSet([trade], LAM_C), ZERO, cfg)
        exact = analytic.xva(trade, Market(ZERO, LAM_C, HazardCurve.flat(cfg.own_hazard)), cfg)
        for view in ("one_bond", "semi_replication"):
            for term, est in out["views"][view].items():
                assert abs(est["value"] - exact[view][term]) < 3 * est["se"], (view, term)

    def test_time_rule_error_is_small_and_second_order(self):
        """Green's second discretisation error, measured on the analytic
        profiles: the midpoint rule on the default cells is within 0.05% and
        quarters when the cells halve."""
        cfg = XvaConfig(hazard_vol=0.0)
        trade = _trade(True)
        market = Market(ZERO, LAM_C, HazardCurve.flat(cfg.own_hazard))
        exact = analytic.xva(trade, market, cfg)["semi_replication"]["dva"]
        errors = []
        for cells in (cfg.cells_per_quarter, 2 * cfg.cells_per_quarter):
            nodes, widths = grid(NettingSet([trade], LAM_C), cfg.settlement_years, cells)
            ene = profiles(trade, ZERO, nodes, cfg.settlement_years, 24)["ene"]
            rate = (1 - cfg.own_recovery) * cfg.own_hazard
            errors.append(-np.sum(widths * rate * kernel("semi_replication", market, cfg, nodes)
                                  * ene) / exact - 1)
        assert abs(errors[0]) < 5e-4
        assert errors[0] / errors[1] == pytest.approx(4.0, rel=0.1)


class TestStochasticHazard:

    @pytest.mark.parametrize("sigma", [0.0, 0.3, 0.8])
    def test_value_today_is_the_pricers_on_every_path(self, sigma):
        trigger = ShiftedTrigger(CirFactor(0.5, sigma), LAM_E)
        trade = _trade(True)
        got = alive_value(trade, trigger, ZERO, 0.0, np.ones(3))
        assert np.allclose(got, value(trade, ZERO, 0.0), rtol=1e-12)

    def test_hazard_volatility_gives_the_buyer_option_value(self):
        """At par and with no lag the deterministic buyer has no CVA; a moving
        hazard makes its MTM positive on some paths."""
        nset = NettingSet([_trade(True, spread="fair")], LAM_C)
        flat = mc.run(nset, ZERO, replace(FAST, hazard_vol=0.0, settlement_days=0))
        vol = mc.run(nset, ZERO, replace(FAST, hazard_vol=0.4, settlement_days=0))
        assert _value(flat, "one_bond", "cva") == 0.0
        assert _value(vol, "one_bond", "cva") < -100.0

    def test_trigger_probability_is_the_markets(self):
        out = mc.run(NettingSet([_trade()], LAM_C), ZERO, XvaConfig(hazard_vol=0.5))
        p = 1 - math.exp(-LAM_E.rates[0] * 5)
        assert abs(out["trigger_probability"]["G1"] - p) < 4 * math.sqrt(p * (1 - p) / 10_000)


class TestNettingAndCollateral:

    def test_offsetting_trades_on_one_gauge_have_no_exposure(self):
        nset = NettingSet([_trade(True), _trade(False)], LAM_C)
        out = mc.run(nset, ZERO, FAST)
        assert _value(out, "one_bond", "cva") == 0.0
        assert _value(out, "one_bond", "fva") == pytest.approx(0.0, abs=1e-6)

    def test_netting_never_costs_more_than_trading_alone(self):
        buy, sell = _trade(True, "G1"), _trade(False, "G2")
        netted = _value(mc.run(NettingSet([buy, sell], LAM_C), ZERO, FAST), "one_bond", "cva")
        apart = _value(mc.run(NettingSet([buy, sell], LAM_C, close_out_netting=False),
                              ZERO, FAST), "one_bond", "cva")
        assert apart <= netted <= 0.0

    def test_without_netting_cva_is_the_sum_of_standalone_cvas(self):
        """Same paths, no netting: exposures and so CVA simply add. Two trades
        on independent gauges use the same factor paths but separate trigger
        draws, so compare against each standalone run on the same draws by
        putting both trades on one gauge."""
        buy, sell = _trade(True, "G1"), _trade(False, "G1")
        apart = _value(mc.run(NettingSet([buy, sell], LAM_C, close_out_netting=False),
                              ZERO, FAST), "one_bond", "cva")
        alone = sum(_value(mc.run(NettingSet([t], LAM_C), ZERO, FAST), "one_bond", "cva")
                    for t in (buy, sell))
        assert apart == pytest.approx(alone, rel=1e-12)

    def test_catalogue_correlation_nets_a_buy_against_a_sell(self):
        weights = np.full(100, 0.01)
        g1, g2 = np.zeros(100, bool), np.zeros(100, bool)
        g1[:20], g2[:20] = True, True                  # the same events take both over
        model = TriggerModel(0.1, weights, {"G1": g1, "G2": g2})
        nset = NettingSet([_trade(True, "G1", "fair"), _trade(False, "G2", "fair")], LAM_C)
        indep = _value(mc.run(nset, ZERO, FAST), "one_bond", "cva")
        shared = _value(mc.run(nset, ZERO, FAST, model=model), "one_bond", "cva")
        assert abs(shared) < 0.7 * abs(indep)

    def test_infinite_threshold_is_uncollateralised(self):
        nset = NettingSet([_trade()], LAM_C)
        base = mc.run(nset, ZERO, FAST)
        huge = mc.run(replace(nset, csa=Csa(True, threshold=1e12)), ZERO, FAST)
        assert _value(huge, "one_bond", "cva") == pytest.approx(_value(base, "one_bond", "cva"),
                                                                 rel=0.05)

    def test_variation_margin_cannot_reach_the_jump_but_initial_margin_can(self):
        """Plan §3.3: VM leaves the notional gap; IM of the notional removes it."""
        nset = NettingSet([_trade(True, spread="fair")], LAM_C)
        cfg = replace(FAST, hazard_vol=0.0)
        vm = mc.run(replace(nset, csa=Csa(True)), ZERO, cfg)
        im = mc.run(replace(nset, csa=Csa(True, im_received=1e7)), ZERO, cfg)
        exact_jump = analytic.xva(nset.trades[0], Market(ZERO, LAM_C, HazardCurve.flat(
            cfg.own_hazard)), cfg)["one_bond"]["cva"]
        # VM leaves at least the uncollateralised jump CVA in place. It adds to it:
        # under the classical lookback, collateral the buyer posted against
        # accrued premium stays frozen while it pays that premium inside the
        # MPoR (Andersen-Pykhtin-Sokol), a limitation recorded in plan §11.
        assert _value(vm, "one_bond", "cva") < 0.9 * exact_jump
        assert abs(_value(im, "one_bond", "cva")) < 0.01 * abs(exact_jump)

    def test_posted_im_raises_dva_benefit_exposure(self):
        nset = NettingSet([_trade(False)], LAM_C)
        base = mc.run(replace(nset, csa=Csa(True)), ZERO, FAST)
        posted = mc.run(replace(nset, csa=Csa(True, im_posted=1e6)), ZERO, FAST)
        assert _value(posted, "semi_replication", "fca") < _value(base, "semi_replication", "fca")


class TestWrongWayRiskAndAllocation:

    def test_beta_zero_weights_are_one_and_weights_average_one(self):
        z = np.array([[0, 1], [1, 1], [0, 0]], dtype=float)
        assert np.all(mc.wwr_weights(z, 0.0) == 1.0)
        assert np.allclose(mc.wwr_weights(z, 2.0).mean(axis=0), 1.0)

    def test_wrong_way_risk_raises_the_buyers_cva(self):
        nset = NettingSet([_trade(True, spread="fair")], LAM_C)
        base = _value(mc.run(nset, ZERO, FAST), "one_bond", "cva")
        stressed = _value(mc.run(nset, ZERO, replace(FAST, wwr_beta=2.0)), "one_bond", "cva")
        assert stressed < 1.5 * base

    def test_allocation_sums_exactly_without_collateral(self):
        nset = NettingSet([_trade(True, "G1"), _trade(False, "G2"), _trade(True, "G3")], LAM_C)
        out = mc.run(nset, ZERO, FAST)
        assert len(out["allocation"]["contributions"]) == 3
        assert out["allocation"]["residual"] == pytest.approx(0.0, abs=1e-8)


class TestRecord:

    def test_reproducible_and_audited(self):
        nset = NettingSet([_trade()], LAM_C)
        a, b = mc.run(nset, ZERO, FAST), mc.run(nset, ZERO, FAST)
        assert a["views"] == b["views"]
        assert a["audit"]["seed"] == FAST.seed and a["audit"]["n_paths"] == 2_000
        assert a["booked"] == a["views"]["one_bond"]
        assert len(a["profiles"]["t"]) == len(a["profiles"]["epe"])

    def test_default_run_uses_ten_thousand_paths(self):
        assert XvaConfig().n_paths == 10_000


class TestPathGuards:

    def test_factor_paths_must_start_at_zero(self):
        from models.xva.paths import factor_paths
        with pytest.raises(ValueError, match="start at 0"):
            factor_paths(CirFactor(0.5, 0.3), np.array([0.5, 1.0]), 2, np.random.default_rng(0))

    def test_alive_value_is_zero_at_maturity(self):
        trigger = ShiftedTrigger(CirFactor(0.5, 0.3), LAM_E)
        assert np.all(alive_value(_trade(), trigger, ZERO, 5.0, np.ones(2)) == 0.0)

    def test_lookup_refuses_times_off_the_grid(self):
        from models.xva.paths import lookup
        with pytest.raises(ValueError, match="not on the simulation grid"):
            lookup(np.array([0.0, 1.0]), np.zeros((2, 2)), np.array([0.5]))
