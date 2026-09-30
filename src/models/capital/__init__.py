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

"""PRS capital relief (MKM-CR-001, proposed; Tier 1).

What a Physical Risk Swap held by a flood-exposed borrower does to that
borrower's probability of default, and so to the lending bank's capital. Two
views, which answer different questions and report different PDs:

- ``one_year``: the one-year PD with and without a PRS -- grade, risk weights,
  default attribution and economics. The PD a master scale and the IRB formula
  are defined on.
- ``over_term``: the cumulative PD over the loan term under four cover modes,
  comparing a PRS embedded in the loan with cover rolled each year.

Every parameter lives in ``config.capital``. ILLUSTRATIVE: not calibrated.
"""

from . import one_year, over_term
from .hazard import flood_losses, prs_payout, simulate_drivers, year_end_liquidity
from .regulatory import grade_for_pd, irb_corporate_rw

__all__ = [
    "one_year",
    "over_term",
    "flood_losses",
    "prs_payout",
    "simulate_drivers",
    "year_end_liquidity",
    "grade_for_pd",
    "irb_corporate_rw",
]
