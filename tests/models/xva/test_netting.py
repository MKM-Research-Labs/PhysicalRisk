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

"""Netting sets and credit support: guards, CDM parsing and the lookback rule."""

import numpy as np
import pytest

from models.xva import HazardCurve, PrsTrade
from models.xva.netting import Csa, NettingSet, close_out_netting_from_cdm, csa_from_cdm

LAM = HazardCurve.flat(0.02)


def _trade(gauge="G1", lam=LAM):
    return PrsTrade(1e7, 0.02, 5, True, lam, gauge)


class TestCsa:

    def test_no_vm_holds_nothing(self):
        assert np.all(Csa().variation_margin_held(np.array([5e6, -5e6])) == 0)

    def test_threshold_and_minimum_transfer(self):
        csa = Csa(True, threshold=1e6, minimum_transfer=2e5)
        held = csa.variation_margin_held(np.array([3e6, 1.1e6, 0.5e6, -3e6]))
        assert held.tolist() == [2e6, 0.0, 0.0, -2e6]

    def test_rejects_negative_amounts(self):
        with pytest.raises(ValueError):
            Csa(True, threshold=-1.0)

    def test_mpor_in_years(self):
        assert Csa(mpor_days=252).mpor_years == 1.0


class TestCdm:

    def test_reads_a_vm_and_im_netting_set(self):
        csa = csa_from_cdm({"CsaType": "VM+IM", "Threshold": 1e6, "MinimumTransferAmount": 1e5,
                            "MarginPeriodOfRiskDays": 20, "InitialMarginReceived": 3e6,
                            "InitialMarginPosted": 1e6})
        assert csa == Csa(True, 1e6, 1e5, 20, 3e6, 1e6)

    def test_vm_only_ignores_initial_margin(self):
        csa = csa_from_cdm({"CsaType": "VM", "InitialMarginReceived": 3e6})
        assert csa.variation_margin and csa.im_received == 0.0 and csa.mpor_days == 10

    def test_missing_or_none_means_uncollateralised(self):
        assert csa_from_cdm(None) == Csa()
        assert not csa_from_cdm({"CsaType": "None"}).variation_margin

    def test_close_out_netting_flag(self):
        assert close_out_netting_from_cdm(None) is True
        assert close_out_netting_from_cdm({"CloseOutNetting": False}) is False


class TestNettingSet:

    def test_horizon_and_gauges(self):
        nset = NettingSet([_trade("G1"), _trade("G2")], LAM)
        assert nset.horizon == 5 and set(nset.gauges) == {"G1", "G2"}

    @pytest.mark.parametrize("kwargs", [
        {"trades": []},
        {"trades": [PrsTrade(1e7, 0.02, 5, True, LAM)]},
        {"trades": [_trade(), _trade(lam=HazardCurve.flat(0.03))]},
        {"trades": [_trade()], "csa": Csa(True), "close_out_netting": False},
    ], ids=["empty", "no-gauge", "inconsistent-hazard", "csa-without-netting"])
    def test_rejects_inconsistent_sets(self, kwargs):
        with pytest.raises(ValueError):
            NettingSet(counterparty=LAM, **kwargs)
