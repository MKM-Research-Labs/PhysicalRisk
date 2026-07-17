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
Delta and revaluation engine for the trading desk.

Sub-modules:
- engine: DeltaEngine class (enrich_trade, revalue_all, build_risk_grid)
- pricer: compute_risky_annuity, compute_gauge_delta, compute_basis_delta,
          compute_mark_to_market

Uses the existing compute_prs_spread() from models.hazard.prs_analytical.
"""

from models.hazard.prs_analytical import compute_prs_spread  # noqa: F401

from .engine import DeltaEngine  # noqa: F401

from .pricer import (  # noqa: F401
    compute_risky_annuity,
    compute_gauge_delta,
    compute_basis_delta,
    compute_mark_to_market,
)

__all__ = [
    'DeltaEngine',
    'compute_prs_spread',
    'compute_risky_annuity',
    'compute_gauge_delta',
    'compute_basis_delta',
    'compute_mark_to_market',
]
