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
Gauge hazard curve — Stress Test tab.

Tab 5: CDS-in-stress cash pricing for PRS trades.
Shows storm scenarios, trade blotter at peak hour, and two chart sub-tabs:
  1. Flood Probability: water level + 3 trigger levels + P(flood)
  2. Stress P&L: water level + stress P&L bars
Fetches from /api/v1/trading/stress/* endpoints.

Sub-modules:
- ghc_stress_setup: State vars, DOM, storm loading, scenario runner, chart switching
- ghc_stress_table: Trade table at peak hour, stats bar, cleanup
- ghc_stress_charts: Flood probability chart, stress P&L chart
"""

from . import ghc_stress_training, ghc_stress_setup, ghc_stress_table, ghc_stress_charts


def get_js() -> str:
    """Return JS fragment for stress test tab."""
    return (ghc_stress_training.get_js() +
            ghc_stress_setup.get_js() +
            ghc_stress_table.get_js() +
            ghc_stress_charts.get_js())
