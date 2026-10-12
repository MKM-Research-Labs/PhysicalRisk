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

"""Netting sets and credit support terms, read from the CDM (WP0 fields).

Collateral follows Green's lookback (6.39): variation margin held at s is set
by the netted value one margin period of risk earlier, less the threshold, and
nothing moves below the minimum transfer amount. Initial margin is a static
segregated amount in each direction (CDM InitialMarginReceived / Posted).
"""

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np

from config.xva import BUSINESS_DAYS_PER_YEAR

from .curves import HazardCurve
from .inputs import PrsTrade


@dataclass(frozen=True)
class Csa:
    """Credit support terms of one netting set."""
    variation_margin: bool = False
    threshold: float = 0.0
    minimum_transfer: float = 0.0
    mpor_days: int = 10
    im_received: float = 0.0
    im_posted: float = 0.0

    def __post_init__(self):
        if min(self.threshold, self.minimum_transfer, self.mpor_days,
               self.im_received, self.im_posted) < 0:
            raise ValueError("credit support amounts must be non-negative")

    @property
    def mpor_years(self) -> float:
        return self.mpor_days / BUSINESS_DAYS_PER_YEAR

    def variation_margin_held(self, lagged_value: np.ndarray) -> np.ndarray:
        """Collateral the bank holds (negative: posts) given the lagged netted value."""
        if not self.variation_margin:
            return np.zeros_like(lagged_value)
        held = np.sign(lagged_value) * np.maximum(np.abs(lagged_value) - self.threshold, 0.0)
        return np.where(np.abs(held) < self.minimum_transfer, 0.0, held)


@dataclass(frozen=True)
class NettingSet:
    """Trades closed out together against one counterparty."""
    trades: Sequence[PrsTrade]
    counterparty: HazardCurve
    csa: Csa = Csa()
    close_out_netting: bool = True

    def __post_init__(self):
        if not self.trades:
            raise ValueError("a netting set needs at least one trade")
        if not self.close_out_netting and (self.csa.variation_margin or self.csa.im_received
                                           or self.csa.im_posted):
            raise ValueError("credit support without close-out netting is not modelled")
        curves: Dict[str, HazardCurve] = {}
        for trade in self.trades:
            if not trade.gauge_id:
                raise ValueError("every trade in a netting set needs a gauge_id")
            first = curves.setdefault(trade.gauge_id, trade.trigger)
            if not (np.array_equal(first.knots, trade.trigger.knots)
                    and np.array_equal(first.rates, trade.trigger.rates)):
                raise ValueError(f"trades on gauge {trade.gauge_id} disagree on its hazard curve")

    @property
    def gauges(self) -> Dict[str, HazardCurve]:
        return {t.gauge_id: t.trigger for t in self.trades}

    @property
    def horizon(self) -> float:
        return max(t.tenor_years for t in self.trades)


def csa_from_cdm(netting_set: Optional[Dict]) -> Csa:
    """Credit support terms from one CDM ``CreditSupport.NettingSets[]`` entry."""
    if not netting_set:
        return Csa()
    csa_type = netting_set.get("CsaType", "None")
    has_vm = csa_type in ("VM", "VM+IM")
    has_im = csa_type == "VM+IM"
    return Csa(
        variation_margin=has_vm,
        threshold=float(netting_set.get("Threshold", 0.0) or 0.0),
        minimum_transfer=float(netting_set.get("MinimumTransferAmount", 0.0) or 0.0),
        mpor_days=int(netting_set.get("MarginPeriodOfRiskDays", 10) or 10),
        im_received=float(netting_set.get("InitialMarginReceived", 0.0) or 0.0) if has_im else 0.0,
        im_posted=float(netting_set.get("InitialMarginPosted", 0.0) or 0.0) if has_im else 0.0,
    )


def close_out_netting_from_cdm(netting_set: Optional[Dict]) -> bool:
    return bool(netting_set.get("CloseOutNetting", True)) if netting_set else True
