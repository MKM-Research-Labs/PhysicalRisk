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
Gauge hazard curve — PRS Pricing tab.

Tab 3: Controls, analytical pricer (semi-annual cashflows),
PRS pricing table + bar chart, and trade commit.

Sub-modules:
- ghc_prs_rates: Yield curve, maturity dates, survival interpolation
- ghc_prs_controls: Input form + maturity popup
- ghc_prs_pricer: Cashflow engine + chart rendering
- ghc_prs_commit: Trade commit API call
"""

from . import ghc_prs_rates, ghc_prs_controls, ghc_prs_pricer, ghc_prs_commit


def get_js() -> str:
    """Return JS fragment for PRS pricing tab."""
    return (ghc_prs_rates.get_js() +
            ghc_prs_controls.get_js() +
            ghc_prs_pricer.get_js() +
            ghc_prs_commit.get_js())
