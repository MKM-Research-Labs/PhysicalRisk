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
Page 10: PRS Pricing
Physical Risk Swap spread table by tenor and threshold from hazard curve data.
"""

from typing import Any, Dict, List

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from .gauge_page_00_base import GaugeBasePage


class GaugePRSPricingPage(GaugeBasePage):
    """Generates PRS pricing page from gauge hazard curve data."""

    TENORS = [1, 2, 3, 5, 7, 10]

    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        elements = []
        elements.append(Paragraph("PRS Pricing Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        hc = gauge_data.get('hazard_curve', {})
        if not hc:
            elements.append(Paragraph(
                "No hazard curve data available. Run: python phys.py port --hazard",
                self.styles['Normal']
            ))
            return elements

        # Compute PRS spreads from annual hazard rates using analytical CDS approximation
        # spread = (1 - recovery) * annual_prob * 10000 bps (simplified)
        recovery = 0.0
        risk_free = 0.03

        thresholds = {
            'Alert': hc.get('annual_hazard_rate_alert', 0),
            'Warning': hc.get('annual_hazard_rate_warning', 0),
            'Severe': hc.get('annual_hazard_rate_severe', 0),
        }

        elements.append(Paragraph("PRS Spread by Tenor and Threshold (bps)", self.styles['SubSectionHeader']))

        header = ['Tenor'] + list(thresholds.keys())
        rows = [header]
        for tenor in self.TENORS:
            row = [f"{tenor}yr"]
            for name, annual_prob in thresholds.items():
                if annual_prob > 0:
                    # Analytical CDS: protection_leg / risky_annuity
                    hazard = annual_prob
                    risky_annuity = sum(
                        1.0 / ((1 + risk_free) ** t) * ((1 - hazard) ** t)
                        for t in range(1, tenor + 1)
                    )
                    survival = (1 - hazard) ** tenor
                    protection = (1 - recovery) * (1 - survival)
                    spread_bps = (protection / risky_annuity * 10000) if risky_annuity > 0 else 0
                    row.append(f"{spread_bps:.1f}")
                else:
                    row.append('N/A')
            rows.append(row)

        table = Table(rows, colWidths=[1.5 * inch, 2 * inch, 2 * inch, 2 * inch])
        table.setStyle(self.table_styles['standard'])
        elements.append(table)
        elements.append(Spacer(1, self.spacing['minor_section']))

        # Key metrics summary
        elements.append(Paragraph("Key Metrics", self.styles['SubSectionHeader']))
        metrics = [
            ['Metric', 'Value'],
            ['Risk-Free Rate', f"{risk_free:.1%}"],
            ['Pricing Model', 'Analytical CDS Approximation'],
        ]
        table = Table(metrics, colWidths=self.table_widths['two_col'])
        table.setStyle(self.table_styles['standard'])
        elements.append(table)

        return elements
