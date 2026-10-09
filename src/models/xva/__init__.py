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

"""PRS XVA (MKM-XV-001, proposed; Tier 1).

Credit, funding and capital valuation adjustments on a Physical Risk Swap,
after Green (2015). An overlay on the PRS pricer (MKM-PR-001), which it
reproduces at t = 0 and does not change. WP1 provides the analytic engine:
one trade, deterministic flood hazard, independence, no collateral. See
``docs/xva/project_plan.md``. Every parameter lives in ``config.xva``.
ILLUSTRATIVE: credit and funding inputs are placeholders.
"""

from . import analytic
from .curves import HazardCurve, ZeroCurve, bootstrap_cds, cds_par_spread, flat_cds_curve
from .inputs import Market, PrsTrade, build_market

__all__ = [
    "analytic",
    "HazardCurve",
    "ZeroCurve",
    "bootstrap_cds",
    "cds_par_spread",
    "flat_cds_curve",
    "Market",
    "PrsTrade",
    "build_market",
]
