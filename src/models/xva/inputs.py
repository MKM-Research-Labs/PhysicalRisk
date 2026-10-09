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

"""What the XVA model prices: one PRS, and the market it is priced in."""

from dataclasses import dataclass
from typing import Optional

from config.xva import RATING_CDS_SPREADS, XvaConfig

from .curves import HazardCurve, ZeroCurve, flat_cds_curve


@dataclass(frozen=True)
class PrsTrade:
    """One gauge PRS from the bank's side.

    ``bank_buys_protection`` is the CDM ``LegData.Payer`` flag: the bank pays
    the spread and is owed the notional on a trigger. The contract follows the
    pricer (D-10): quarterly premium in arrears, paid only if no trigger has
    occurred by the payment date; protection to the first trigger; recovery 0.
    """
    notional: float
    spread: float                    # running spread, decimal (50bp = 0.0050)
    tenor_years: float               # whole quarters from the valuation date
    bank_buys_protection: bool
    trigger: HazardCurve             # flood-trigger intensity lambda_E
    gauge_id: str = ""               # reference gauge; links trades in the Monte Carlo

    def __post_init__(self):
        if self.notional <= 0 or self.tenor_years <= 0:
            raise ValueError("notional and tenor_years must be positive")
        quarters = self.tenor_years * 4
        if abs(quarters - round(quarters)) > 1e-9:
            raise ValueError("tenor_years must be a whole number of quarters")

    @property
    def direction(self) -> float:
        return 1.0 if self.bank_buys_protection else -1.0


@dataclass(frozen=True)
class Market:
    """The curves the adjustments are integrated against."""
    zero: ZeroCurve
    counterparty: HazardCurve        # lambda_C
    own: HazardCurve                 # lambda_B (semi-replication kernel and DVA/FCA)


def build_market(zero: ZeroCurve, cfg: XvaConfig, *, rating: Optional[str] = None,
                 counterparty: Optional[HazardCurve] = None) -> Market:
    """Assemble the market from a counterparty curve or a rating proxy (D-11).

    The bank's hazard comes from its funding spread with no bond-CDS basis
    (``XvaConfig.own_hazard``).
    """
    if (rating is None) == (counterparty is None):
        raise ValueError("give exactly one of rating or counterparty")
    if counterparty is None:
        if rating not in RATING_CDS_SPREADS:
            raise ValueError(f"no proxy spread for rating {rating!r}")
        counterparty = flat_cds_curve(RATING_CDS_SPREADS[rating],
                                      cfg.counterparty_recovery, zero)
    return Market(zero=zero, counterparty=counterparty, own=HazardCurve.flat(cfg.own_hazard))
