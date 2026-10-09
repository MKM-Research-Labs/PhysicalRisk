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

"""Counterparty capital (D-07): SA-CCR against the Basel Committee's own worked
examples, and BA-CVA, risk weights and the guards against hand-worked figures.

The SA-CCR figures are BCBS 279 (March 2014), Annex 4a, Examples 2, 3 and 5,
copied from the published document. Basel rounds every intermediate figure,
so each is compared to the printed precision.
"""

import math

import numpy as np
import pytest

from config.counterparty_capital import (
    SACCR_COMMODITY_CORRELATION,
    SACCR_COMMODITY_SF,
    SACCR_CREDIT_INDEX_CORRELATION,
    SACCR_CREDIT_INDEX_SF,
    SACCR_CREDIT_SF,
    SACCR_CREDIT_SINGLE_NAME_CORRELATION,
)
from models.capital.counterparty import (
    aggregate_addon,
    ba_cva_discount,
    ba_cva_maturity,
    ba_cva_reduced,
    ba_cva_risk_weight,
    commodity_addon,
    ead,
    letter_grade,
    maturity_factor_margined,
    maturity_factor_unmargined,
    pfe_multiplier,
    replacement_cost,
    sa_risk_weight,
    scva,
    supervisory_duration,
)


class TestBaselExample2Credit:
    """Unmargined: long CDS Firm A (AA, 3y), short Firm B (BBB, 6y), long CDX.IG (5y)."""

    NOTIONAL = 10_000
    VALUE = 20 - 40 + 0

    def _entity_addons(self):
        sd = supervisory_duration(0.0, np.array([3.0, 6.0, 5.0]))
        adjusted = self.NOTIONAL * sd
        assert np.round(sd, 2).tolist() == [2.79, 5.18, 4.42]
        assert np.round(adjusted).tolist() == [27_858, 51_836, 44_240]
        delta = np.array([1.0, -1.0, 1.0])
        sf = np.array([SACCR_CREDIT_SF["AA"], SACCR_CREDIT_SF["BBB"], SACCR_CREDIT_INDEX_SF["IG"]])
        return sf * delta * adjusted * maturity_factor_unmargined(np.array([3.0, 6.0, 5.0]))

    def test_entity_addons(self):
        assert np.round(self._entity_addons()).tolist() == [106, -280, 168]

    def test_aggregate_addon_multiplier_and_ead(self):
        rho = [SACCR_CREDIT_SINGLE_NAME_CORRELATION] * 2 + [SACCR_CREDIT_INDEX_CORRELATION]
        addon = aggregate_addon(list(self._entity_addons()), rho)
        assert round(float(addon)) == 282
        assert replacement_cost(self.VALUE, 0.0) == 0.0
        assert round(float(pfe_multiplier(self.VALUE, 0.0, addon)), 3) == 0.965
        assert round(float(ead(self.VALUE, 0.0, addon))) == 381


class TestBaselExample3Commodity:
    """Unmargined: long WTI 9m 10,000; short Brent 2y 20,000; long silver 5y 10,000."""

    def test_effective_notional_addons_and_ead(self):
        mf = maturity_factor_unmargined(np.array([0.75, 2.0, 5.0]))
        assert mf[0] == pytest.approx(math.sqrt(9 / 12))
        crude = 1 * 10_000 * mf[0] - 1 * 20_000 * mf[1]
        assert round(abs(crude)) == 11_340
        addon = commodity_addon({"energy": {"crude_oil": crude},
                                 "metals": {"silver": 10_000 * mf[2]}},
                                {"energy": SACCR_COMMODITY_SF["oil_gas"],
                                 "metals": SACCR_COMMODITY_SF["metals"]},
                                SACCR_COMMODITY_CORRELATION)
        assert round(float(addon)) == 2_041 + 1_800
        value = -50 - 30 + 100
        assert replacement_cost(value, 0.0) == 20
        assert pfe_multiplier(value, 0.0, addon) == 1.0
        assert round(float(ead(value, 0.0, addon))) == 5_406

    def test_one_type_in_a_hedging_set_is_its_own_addon(self):
        assert aggregate_addon([np.array(-2_041.0)], 0.4) == pytest.approx(2_041.0)


class TestBaselExample5Margined:
    """Weekly margin: MPoR 10 + 5 - 1 = 14 days, TH 0, MTA 5, NICA 150, C 200, V 80."""

    def test_replacement_cost(self):
        assert replacement_cost(80.0, 200.0, margined=True, threshold=0.0, mta=5.0,
                                nica=150.0) == 0.0

    def test_margined_maturity_factor_and_crude_notional(self):
        mf = maturity_factor_margined(14)
        assert mf == pytest.approx(1.5 * math.sqrt(14 / 250))
        assert round(abs(10_000 * mf - 20_000 * mf)) == 3_550
        assert round(0.18 * 3_550) == 639


class TestSaccrGuards:

    def test_maturity_factor_floor_is_ten_business_days(self):
        assert maturity_factor_unmargined(0.0) == pytest.approx(math.sqrt(10 / 250))

    def test_no_addon_means_full_multiplier(self):
        assert pfe_multiplier(-100.0, 0.0, 0.0) == 1.0

    def test_margined_ead_is_capped_at_unmargined(self):
        unmargined = ead(0.0, 0.0, 100.0)
        margined = ead(0.0, 0.0, 1_000.0, margined=True, threshold=1e6, unmargined_addon=100.0)
        assert margined == pytest.approx(unmargined)

    def test_margined_ead_needs_the_unmargined_addon(self):
        with pytest.raises(ValueError, match="unmargined add-on"):
            ead(0.0, 0.0, 10.0, margined=True)


class TestRiskWeightsAndBaCva:

    @pytest.mark.parametrize("rating, grade", [("BBB-", "BBB"), ("A+", "A"), ("AAA", "AAA"),
                                               ("NR", "unrated"), ("", "unrated")])
    def test_letter_grade(self, rating, grade):
        assert letter_grade(rating) == grade

    def test_sa_risk_weights(self):
        assert sa_risk_weight("BBB-") == 0.75
        assert sa_risk_weight("A", "bank") == 0.30
        assert sa_risk_weight("NR") == 1.00

    def test_ba_cva_risk_weight_by_grade(self):
        assert ba_cva_risk_weight("financials", "A") == 0.05
        assert ba_cva_risk_weight("financials", "BB+") == 0.12

    def test_discount_factor(self):
        assert ba_cva_discount(0.0) == 1.0
        assert ba_cva_discount(5.0) == pytest.approx((1 - math.exp(-0.25)) / 0.25)

    def test_netting_set_maturity_is_notional_weighted_and_floored(self):
        m = ba_cva_maturity([np.array([4.0, 0.5]), np.array([2.0, 0.5])],
                            [np.array([1.0, 1.0]), np.array([3.0, 1.0])])
        assert m.tolist() == [2.5, 1.0]
        assert ba_cva_maturity([np.array([3.0])], [np.array([0.0])]).tolist() == [0.0]

    def test_single_counterparty_reduced_is_ds_times_scva(self):
        """Hand-worked: RW 5%, M 3, EAD 1m: SCVA = 0.05 x 3 x 1e6 x DF(3) / 1.4."""
        s = scva(0.05, 1e6, 3.0)
        assert s == pytest.approx(0.05 * 3 * 1e6 * (1 - math.exp(-0.15)) / 0.15 / 1.4)
        assert ba_cva_reduced({"c": np.array(s)}) == pytest.approx(0.65 * s)

    def test_two_counterparties_diversify(self):
        k = ba_cva_reduced({"a": np.array(100.0), "b": np.array(100.0)})
        assert k == pytest.approx(0.65 * math.sqrt((0.5 * 200) ** 2 + 0.75 * 2 * 100 ** 2))
