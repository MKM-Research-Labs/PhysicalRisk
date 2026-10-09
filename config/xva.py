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

"""
PRS XVA parameters (MKM-XV-001, proposed; Tier 1).

Every number the XVA model uses: the funding strategy and close-out choices,
the bank's own funding curve, the counterparty credit proxy, the settlement
lag, the numerical settings, and the capital cost shared with MKM-CR-001.
The design and the decisions behind each value are in
``docs/xva/project_plan.md`` (sections 4.4 and 9, decisions D-01 to D-13).

ILLUSTRATIVE. The rating-to-spread proxy (D-11) and the bank's funding spread
(D-12) are placeholders with no owner yet; they make the engine runnable and
must be replaced before any figure is used for a decision.

The dataclass is frozen and its field names are part of the audit record:
``fingerprint()`` hashes them.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Dict, Tuple

from config.capital import CapitalConfig
from config.port import PRS_SETTLEMENT_DAYS

STATUS = "ILLUSTRATIVE - credit and funding inputs are placeholders (D-11, D-12)"

#: Funding strategies (Green Ch. 9). ``one_bond``: unilateral CVA + symmetric
#: FVA, discounted at r_F + lambda_C (9.64-9.67). ``semi_replication``: the
#: no-shortfall strategy, CVA + DVA + FCA, discounted at r + lambda_B +
#: lambda_C (9.55-9.59). D-01 books ``one_bond`` and shows the other beside it.
FUNDING_STRATEGIES: Tuple[str, ...] = ("one_bond", "semi_replication")

#: Business days in a year, used to turn a settlement lag into a year fraction.
BUSINESS_DAYS_PER_YEAR = 252

#: Placeholder counterparty CDS spreads by rating, flat across tenors (D-11,
#: open). Shaped like a generic corporate curve; not sourced from any market.
RATING_CDS_SPREADS: Dict[str, float] = {
    "AAA": 0.0020, "AA+": 0.0025, "AA": 0.0030, "AA-": 0.0035,
    "A+": 0.0045, "A": 0.0055, "A-": 0.0065,
    "BBB+": 0.0090, "BBB": 0.0120, "BBB-": 0.0160,
    "BB+": 0.0230, "BB": 0.0300, "BB-": 0.0380,
    "B+": 0.0480, "B": 0.0600, "B-": 0.0750,
    "CCC": 0.1100,
}

_CAPITAL = CapitalConfig()


@dataclass(frozen=True)
class XvaConfig:
    """Everything the analytic engine needs besides the trade and the curves."""
    funding_strategy: str = "one_bond"           # D-01
    counterparty_recovery: float = 0.40          # R_C
    own_funding_spread: float = 0.0075           # s_F, placeholder (D-12)
    own_recovery: float = 0.40                   # R_B; lambda_B = s_F / (1 - R_B)
    settlement_days: int = PRS_SETTLEMENT_DAYS   # D-09, provisional
    cost_of_capital: float = _CAPITAL.cost_of_equity   # gamma_K, D-06
    capital_funding_fraction: float = 0.0        # phi, D-06
    quadrature_nodes: int = 24                   # Gauss-Legendre nodes per sub-interval
    profile_step_years: float = 1.0 / 12.0       # reporting grid for exposure profiles

    def __post_init__(self):
        if self.funding_strategy not in FUNDING_STRATEGIES:
            raise ValueError(f"funding_strategy must be one of {FUNDING_STRATEGIES}")
        for name in ("counterparty_recovery", "own_recovery", "capital_funding_fraction"):
            if not 0.0 <= getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.own_recovery >= 1.0 and self.own_funding_spread > 0:
            raise ValueError("own_recovery of 1 implies no own default; s_F must be 0")
        if self.settlement_days < 0 or self.own_funding_spread < 0:
            raise ValueError("settlement_days and own_funding_spread must be non-negative")

    @property
    def settlement_years(self) -> float:
        return self.settlement_days / BUSINESS_DAYS_PER_YEAR

    @property
    def own_hazard(self) -> float:
        """lambda_B from the funding spread, assuming no bond-CDS basis (Green 9.16)."""
        if self.own_funding_spread == 0.0:
            return 0.0
        return self.own_funding_spread / (1.0 - self.own_recovery)

    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()
