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
Page 8: Flood History
50-year historical water level graph with warning thresholds,
plus top worst storm scenarios table.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer

from ..gauge_page_00_base import GaugeBasePage
from ._builders import _FloodHistoryBuildersMixin


class GaugeFloodHistoryPage(_FloodHistoryBuildersMixin, GaugeBasePage):
    """Generates flood history page with historical graph and worst storms."""

    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        elements = []
        elements.append(Paragraph("Flood History", self.styles['SectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        # --- Section 1: Historical Water Level Graph ---
        hd = (timeseries_data or {}).get('historical_daily')
        if hd and hd.get('daily_observations'):
            elements.extend(self._build_historical_graph(hd))
        else:
            elements.append(Paragraph(
                "No historical daily data available for this gauge.",
                self.styles['Normal']
            ))

        # --- Section 1b: Realised Flood Events ---
        if hd and hd.get('daily_observations'):
            elements.append(Spacer(1, self.spacing['major_section']))
            elements.extend(self._build_realised_floods(hd))

        elements.append(Spacer(1, self.spacing['major_section']))

        # --- Section 2: Top Worst Storm Scenarios ---
        storm_responses = []
        if timeseries_data:
            storm_responses = timeseries_data.get('storm_responses', [])

        if storm_responses:
            elements.extend(self._build_worst_storms_table(storm_responses))
        else:
            elements.append(Paragraph(
                "No storm response data available.",
                self.styles['Normal']
            ))

        return elements
