# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Page 9: Hazard Curves
GEV-fitted hazard curve data — return periods, exceedance probabilities.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from .gauge_page_00_base import GaugeBasePage


class GaugeHazardCurvesPage(GaugeBasePage):
    """Generates hazard curve summary page from gaugehc.json data."""

    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        elements = []
        elements.append(Paragraph("Hazard Curve Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        # Extract hazard curve data (passed via timeseries_data or gauge_data)
        hc = gauge_data.get('hazard_curve', {})
        if not hc:
            elements.append(Paragraph(
                "No hazard curve data available. Run: python app.py port --hazard",
                self.styles['Normal']
            ))
            return elements

        # GEV Parameters
        elements.append(Paragraph("GEV Distribution Parameters", self.styles['SubSectionHeader']))
        gev_rows = [
            ['Parameter', 'Value'],
            ['Location (mu)', self._format_value(hc.get('gev_location', 'N/A'))],
            ['Scale (sigma)', self._format_value(hc.get('gev_scale', 'N/A'))],
            ['Shape (xi)', self._format_value(hc.get('gev_shape', 'N/A'))],
        ]
        table = Table(gev_rows, colWidths=self.table_widths['two_col'])
        table.setStyle(self.table_styles['standard'])
        elements.append(table)
        elements.append(Spacer(1, self.spacing['minor_section']))

        # Annual Hazard Rates
        elements.append(Paragraph("Annual Hazard Rates", self.styles['SubSectionHeader']))
        rate_rows = [
            ['Threshold', 'Annual Probability', 'Return Period'],
            ['Alert', f"{hc.get('annual_hazard_rate_alert', 0):.4f}",
             f"{1/hc['annual_hazard_rate_alert']:.0f} yr" if hc.get('annual_hazard_rate_alert', 0) > 0 else 'N/A'],
            ['Warning', f"{hc.get('annual_hazard_rate_warning', 0):.4f}",
             f"{1/hc['annual_hazard_rate_warning']:.0f} yr" if hc.get('annual_hazard_rate_warning', 0) > 0 else 'N/A'],
            ['Severe', f"{hc.get('annual_hazard_rate_severe', 0):.4f}",
             f"{1/hc['annual_hazard_rate_severe']:.0f} yr" if hc.get('annual_hazard_rate_severe', 0) > 0 else 'N/A'],
        ]
        table = Table(rate_rows, colWidths=self.table_widths['three_col'])
        table.setStyle(self.table_styles['flood_risk'])
        elements.append(table)
        elements.append(Spacer(1, self.spacing['minor_section']))

        # Return Period Levels
        rpl = hc.get('return_period_levels', {})
        if rpl:
            elements.append(Paragraph("Return Period Water Levels", self.styles['SubSectionHeader']))
            rp_rows = [['Return Period', 'Water Level (m)']]
            for period in ['2yr', '5yr', '10yr', '20yr', '50yr', '100yr']:
                if period in rpl:
                    rp_rows.append([period, f"{rpl[period]:.3f}"])
            table = Table(rp_rows, colWidths=self.table_widths['two_col'])
            table.setStyle(self.table_styles['standard'])
            elements.append(table)

        return elements
