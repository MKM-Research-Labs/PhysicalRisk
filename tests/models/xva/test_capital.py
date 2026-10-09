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

"""Capital per Monte Carlo state and KVA (WP3).

Capital today is checked against hand-worked SA-CCR, BA-CVA and RRAO figures.
KVA is checked against the integral of a capital profile that is known
exactly, and the properties the regulatory treatment implies.
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from config.xva import XvaConfig
from models.xva import HazardCurve, PrsTrade, ZeroCurve
from models.xva import monte_carlo as mc
from models.xva.capital import CounterpartyProfile, capital
from models.xva.integrals import kernel
from models.xva.inputs import Market
from models.xva.netting import Csa, NettingSet
from models.xva.valuation import fair_spread

from ._fixtures import HUMPED

ZERO = ZeroCurve(HUMPED)
LAM_E = HazardCurve.from_annual_probability(0.02)
LAM_C = HazardCurve.flat(0.02)
PROFILE = CounterpartyProfile("BBB", "corporate", "financials")
FAST = XvaConfig(n_paths=2_000)
N = 1e7
RATIO = FAST.capital_ratio
SCALE = RATIO / 0.08
DF5 = (1 - math.exp(-0.25)) / 0.25


def _at_par(buyer=True, gauge="G1", trigger=LAM_E):
    t = PrsTrade(N, 0.01, 5, buyer, trigger, gauge)
    return replace(t, spread=fair_spread(t, ZERO))


def _today(cfg=FAST, csa=Csa(), trades=None):
    nset = NettingSet(trades or [_at_par()], LAM_C, csa)
    return mc.run(nset, ZERO, cfg, counterparty=PROFILE)["kva"]["today"]


class TestCapitalToday:
    """At the fair spread V(0) = 0, so the PFE multiplier is exactly 1."""

    def test_commodity_treatment(self):
        today = _today()
        ead = 1.4 * 0.18 * N
        assert today["ead"] == pytest.approx(ead, rel=1e-9)
        assert today["ccr"] == pytest.approx(RATIO * 0.75 * ead, rel=1e-9)
        assert today["cva"] == pytest.approx(SCALE * 0.65 * 0.05 * 5 * ead * DF5 / 1.4, rel=1e-9)
        assert today["rrao"] == 0.0

    def test_credit_treatment(self):
        today = _today(replace(FAST, saccr_asset_class="credit_single_name"))
        sd = (1 - math.exp(-0.25)) / 0.05
        assert today["ead"] == pytest.approx(1.4 * 0.016 * N * sd, rel=1e-9)

    def test_rrao_switch(self):
        assert _today(replace(FAST, rrao=True))["rrao"] == pytest.approx(SCALE * 0.01 * N)

    def test_variation_margin_uses_the_margined_maturity_factor(self):
        today = _today(csa=Csa(True))
        assert today["ead"] == pytest.approx(1.4 * 0.18 * N * 1.5 * math.sqrt(10 / 250), rel=1e-9)

    def test_offsetting_trades_on_one_gauge_need_no_capital(self):
        today = _today(trades=[_at_par(True), _at_par(False)])
        assert today["ead"] == 0.0 and today["ccr"] == 0.0 and today["cva"] == 0.0

    def test_bank_counterparty_weight(self):
        bank = CounterpartyProfile("BBB", "bank", "financials")
        nset = NettingSet([_at_par()], LAM_C)
        today = mc.run(nset, ZERO, FAST, counterparty=bank)["kva"]["today"]
        assert today["ccr"] == pytest.approx(RATIO * 0.50 * today["ead"], rel=1e-12)


class TestCapitalPerState:

    def test_settled_trades_carry_nothing(self):
        nset = NettingSet([_at_par()], LAM_C)
        out = capital(nset, PROFILE, nodes=np.array([1.0]), alive=np.zeros((1, 3, 1), bool),
                      net=np.zeros((3, 1)), collateral=np.zeros((3, 1)), asset_class="commodity_other",
                      reference_rating="B", rrao=True, capital_ratio=RATIO)
        assert all(np.all(v == 0.0) for v in out.values())

    def test_pending_payout_counts_as_replacement_cost_only(self):
        nset = NettingSet([_at_par()], LAM_C)
        out = capital(nset, PROFILE, nodes=np.array([1.0]), alive=np.zeros((1, 1, 1), bool),
                      net=np.array([[N]]), collateral=np.zeros((1, 1)),
                      asset_class="commodity_other", reference_rating="B", rrao=False,
                      capital_ratio=RATIO)
        assert out["ead"][0, 0] == pytest.approx(1.4 * N)


class TestKva:

    def test_matches_the_integral_of_a_known_capital_profile(self):
        """With no trigger risk and sigma = 0, capital is deterministic: KVA is
        exactly the integral of its profile, with no Monte Carlo error."""
        trade = _at_par(trigger=HazardCurve.flat(1e-12))
        cfg = replace(FAST, hazard_vol=0.0)
        out = mc.run(NettingSet([trade], LAM_C), ZERO, cfg, counterparty=PROFILE)["kva"]
        from models.xva.paths import grid
        nodes, widths = grid(NettingSet([trade], LAM_C), cfg.settlement_years, cfg.cells_per_quarter)
        k = np.array(out["profiles"]["ccr"]) + np.array(out["profiles"]["cva"])
        market = Market(ZERO, LAM_C, HazardCurve.flat(cfg.own_hazard))
        expected = -np.sum(widths * cfg.cost_of_capital * kernel("one_bond", market, cfg, nodes) * k)
        assert out["total"]["value"] == pytest.approx(expected, rel=1e-10)
        assert out["total"]["se"] == pytest.approx(0.0, abs=1e-6)

    def test_reported_but_not_booked(self):
        out = mc.run(NettingSet([_at_par()], LAM_C), ZERO, FAST, counterparty=PROFILE)
        assert out["kva"]["included_in_booked"] is False
        assert set(out["booked"]) == {"cva", "fva", "total"}
        assert out["kva"]["total"]["value"] < 0

    def test_funding_from_capital_lowers_kva(self):
        nset = NettingSet([_at_par()], LAM_C)
        gross = mc.run(nset, ZERO, FAST, counterparty=PROFILE)["kva"]["total"]["value"]
        net = mc.run(nset, ZERO, replace(FAST, capital_funding_fraction=1.0),
                     counterparty=PROFILE)["kva"]["total"]["value"]
        assert abs(net) < abs(gross)

    def test_no_counterparty_profile_means_no_kva(self):
        assert "kva" not in mc.run(NettingSet([_at_par()], LAM_C), ZERO, FAST)

    def test_rejects_an_unknown_asset_class(self):
        with pytest.raises(ValueError, match="saccr_asset_class"):
            XvaConfig(saccr_asset_class="weather")
