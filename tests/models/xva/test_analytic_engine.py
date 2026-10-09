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

"""The engine's output: the run record, the break-even spread, KVA's integral,
configuration guards and the rating-proxy market."""

import math
from dataclasses import replace

import numpy as np
import pytest

from config.xva import RATING_CDS_SPREADS, XvaConfig
from models.xva import HazardCurve, PrsTrade, ZeroCurve, analytic, build_market
from models.xva.integrals import Grid, kva
from models.xva.valuation import fair_spread, value

from ._fixtures import HUMPED, NOTIONAL, case


class TestRun:

    def test_record_shape_and_booked_view(self):
        trade, market, cfg, _ = case(curve=HUMPED)
        out = analytic.run(trade, market, cfg)
        assert out["booked_strategy"] == "one_bond"
        assert out["booked"] == out["views"]["one_bond"]
        assert out["dva_disclosed"] == out["views"]["semi_replication"]["dva"]
        assert out["audit"]["config_sha256"] == cfg.fingerprint()
        assert out["audit"]["status"].startswith("ILLUSTRATIVE")
        assert len(out["profiles"]["t"]) == len(out["profiles"]["epe"]) == 61

    def test_semi_replication_can_be_booked(self):
        trade, market, cfg, _ = case(funding_strategy="semi_replication")
        out = analytic.run(trade, market, cfg, solve_spread=False)
        assert out["booked"] == out["views"]["semi_replication"]
        assert "all_in_spread_bps" not in out

    def test_profiles_bound_the_expected_exposure(self):
        trade, market, cfg, _ = case(curve=HUMPED, buyer=False)
        p = analytic.run(trade, market, cfg, solve_spread=False)["profiles"]
        epe, ene, ee = map(np.array, (p["epe"], p["ene"], p["ee"]))
        assert np.all(epe >= 0) and np.all(ene <= 0)
        assert np.allclose(epe + ene, ee)


class TestBreakEvenSpread:

    @pytest.mark.parametrize("buyer", [True, False])
    def test_value_plus_xva_is_zero_at_the_all_in_spread(self, buyer):
        trade, market, cfg, _ = case(buyer=buyer, curve=HUMPED, lam_c=0.05)
        out = analytic.run(trade, market, cfg)
        at = replace(trade, spread=out["all_in_spread_bps"] / 1e4)
        total = value(at, market.zero, 0.0) + analytic.xva(at, market, cfg)["one_bond"]["total"]
        assert abs(total) < 1e-4

    @staticmethod
    def _at_fair(buyer):
        trade, market, cfg, _ = case(buyer=buyer, curve=HUMPED, lam_c=0.05)
        trade = replace(trade, spread=fair_spread(trade, market.zero))
        return trade, market, cfg

    @pytest.mark.parametrize("buyer", [True, False])
    def test_first_order_approximation_is_close(self, buyer):
        """At the fair spread, s* - s_fair ~ U / (direction N A) with U held fixed.

        The approximation is close but not exact, and for the seller it is
        biased low: a wider spread enlarges what the buyer owes, so CVA grows
        with the spread (about 9% here). That is why the engine solves exactly.
        """
        trade, market, cfg = self._at_fair(buyer)
        out = analytic.run(trade, market, cfg)
        first_order = out["booked"]["total"] / (trade.direction * NOTIONAL
                                                 * out["risky_annuity"]) * 1e4
        assert out["xva_spread_bps"] == pytest.approx(first_order, rel=0.15)
        if not buyer:
            assert out["xva_spread_bps"] > first_order

    def test_seller_at_fair_charges_more_for_its_xva_cost(self):
        trade, market, cfg = self._at_fair(False)
        out = analytic.run(trade, market, cfg)
        assert out["booked"]["total"] < 0 and out["xva_spread_bps"] > 0


class TestKva:

    def test_constant_capital_has_a_closed_form(self):
        trade, market, cfg, _ = case()
        grid = Grid(trade, market, cfg)
        capital = 1_000_000.0
        got = kva(grid, "one_bond", lambda s: np.full_like(s, capital))
        k = 0.03 + cfg.own_funding_spread + 0.02
        horizon = 5 + cfg.settlement_years
        expected = -cfg.cost_of_capital * capital * (1 - math.exp(-k * horizon)) / k
        assert got == pytest.approx(expected, rel=1e-13)

    def test_funding_from_capital_nets_the_short_rate(self):
        trade, market, cfg, _ = case(capital_funding_fraction=1.0)
        grid = Grid(trade, market, cfg)
        ones = lambda s: np.ones_like(s)
        net = kva(grid, "one_bond", ones)
        gross = kva(Grid(trade, market, replace(cfg, capital_funding_fraction=0.0)),
                    "one_bond", ones)
        assert net / gross == pytest.approx((cfg.cost_of_capital - 0.03) / cfg.cost_of_capital,
                                            rel=1e-12)


class TestInputs:

    def test_rating_proxy_market(self):
        cfg = XvaConfig()
        market = build_market(ZeroCurve(HUMPED), cfg, rating="BBB")
        assert market.counterparty.rates[0] == pytest.approx(
            RATING_CDS_SPREADS["BBB"] / (1 - cfg.counterparty_recovery), rel=0.01)
        assert market.own.rates[0] == pytest.approx(cfg.own_hazard)

    def test_explicit_counterparty_curve(self):
        curve = HazardCurve.flat(0.04)
        assert build_market(ZeroCurve(), XvaConfig(), counterparty=curve).counterparty is curve

    @pytest.mark.parametrize("kwargs", [{}, {"rating": "BBB", "counterparty": HazardCurve.flat(0.1)},
                                        {"rating": "ZZZ"}])
    def test_market_rejects_bad_counterparty_inputs(self, kwargs):
        with pytest.raises(ValueError):
            build_market(ZeroCurve(), XvaConfig(), **kwargs)

    @pytest.mark.parametrize("kwargs", [{"notional": 0}, {"tenor_years": 1.1}, {"tenor_years": 0}])
    def test_trade_rejects_bad_terms(self, kwargs):
        terms = dict(notional=1.0, spread=0.01, tenor_years=1.0, bank_buys_protection=True,
                     trigger=HazardCurve.flat(0.01))
        terms.update(kwargs)
        with pytest.raises(ValueError):
            PrsTrade(**terms)

    @pytest.mark.parametrize("kwargs", [{"funding_strategy": "two_bond"},
                                        {"counterparty_recovery": 1.2},
                                        {"own_recovery": 1.0},
                                        {"settlement_days": -1}])
    def test_config_rejects_bad_values(self, kwargs):
        with pytest.raises(ValueError):
            XvaConfig(**kwargs)

    def test_zero_funding_spread_means_no_own_hazard(self):
        assert XvaConfig(own_funding_spread=0.0).own_hazard == 0.0


class TestGuards:

    @staticmethod
    def _fixed_xva(monkeypatch, total):
        monkeypatch.setattr(analytic, "xva", lambda t, m, c: {"one_bond": {"total": total}})

    def test_break_even_widens_its_bracket(self, monkeypatch):
        """An XVA far larger than the fair spread forces the bracket out."""
        trade, market, cfg = TestBreakEvenSpread._at_fair(False)
        self._fixed_xva(monkeypatch, -1e6)
        s = analytic.break_even_spread(trade, market, cfg)
        assert value(replace(trade, spread=s), market.zero, 0.0) == pytest.approx(1e6, rel=1e-9)

    def test_break_even_gives_up_beyond_any_plausible_spread(self, monkeypatch):
        trade, market, cfg = TestBreakEvenSpread._at_fair(False)
        self._fixed_xva(monkeypatch, -1e12)
        with pytest.raises(ValueError, match="no break-even spread"):
            analytic.break_even_spread(trade, market, cfg)

    def test_unknown_strategy_has_no_kernel(self):
        from models.xva.integrals import kernel
        trade, market, cfg, _ = case()
        with pytest.raises(ValueError, match="unknown funding strategy"):
            kernel("two_bond", market, cfg, np.array([1.0]))
