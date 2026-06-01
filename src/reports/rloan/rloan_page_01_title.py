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
Page 1: Mortgage Report Title and Property Context
"""

from datetime import datetime
from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from reports.property.property_page_00_base import PropertyBasePage


class RLoanTitlePage(PropertyBasePage):
    """Title page for residential-loan report with property context."""

    def generate_elements(self, property_data: Dict[str, Any],
                         rloan_data: Dict[str, Any] = None) -> List:
        elements = []

        try:
            # Extract IDs
            mortgage_id = 'Unknown'
            provider = 'N/A'
            app_date = 'N/A'
            if rloan_data:
                mort = rloan_data.get('RLoan', rloan_data)
                hdr = mort.get('Header', {})
                mortgage_id = hdr.get('RLoanID', 'Unknown')
                app = mort.get('Application', {})
                provider = app.get('MortgageProvider', 'N/A')
                app_date = app.get('ApplicationDate', 'N/A')

            ph = property_data.get('PropertyHeader', {})
            prop_header = ph.get('Header', {})
            property_id = prop_header.get('PropertyID', 'Unknown')

            # Title
            elements.append(Paragraph(
                "Comprehensive Mortgage Analysis Report",
                self.styles['Title']
            ))
            elements.append(Paragraph(
                f"Mortgage ID: {mortgage_id}",
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                f"Report Date: {datetime.now().strftime('%Y-%m-%d')}",
                self.styles['Normal']
            ))
            elements.append(Spacer(1, self.spacing['major_section']))

            # Mortgage summary
            elements.append(Paragraph("Mortgage Summary", self.styles['SectionHeader']))
            mort_summary = [["Mortgage Information", "Value"]]
            mort_summary.append(["Mortgage ID", mortgage_id])
            mort_summary.append(["Provider", provider])
            mort_summary.append(["Application Date", app_date])
            mort_summary.append(["Property ID", property_id])

            if rloan_data:
                mort = rloan_data.get('RLoan', rloan_data)
                fin = mort.get('FinancialTerms', {})
                cur = mort.get('CurrentStatus', {})
                if fin.get('OriginalLoan'):
                    mort_summary.append(["Original Loan", f"£{fin['OriginalLoan']:,.2f}"])
                if cur.get('OutstandingBalance'):
                    mort_summary.append(["Outstanding Balance", f"£{cur['OutstandingBalance']:,.2f}"])
                if fin.get('OriginalLTV'):
                    ltv = fin['OriginalLTV']
                    ltv_str = f"{ltv*100:.1f}%" if ltv < 1 else f"{ltv:.1f}%"
                    mort_summary.append(["Original LTV", ltv_str])
                if fin.get('MaturityDate'):
                    mort_summary.append(["Maturity Date", fin['MaturityDate']])

            table = Table(mort_summary, colWidths=self.table_widths['two_col'])
            table.setStyle(self.table_styles['standard'])
            elements.append(table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # Property context
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Property Context", self.styles['SectionHeader']))

            loc = ph.get('Location', {})
            attrs = ph.get('PropertyAttributes', {})
            risk = loc.get('RiskAssessment', ph.get('RiskAssessment', {}))
            val = ph.get('Valuation', {})

            prop_info = [["Property Detail", "Value"]]
            prop_info.append(["Property ID", property_id])

            address = loc.get('FullAddress', 'N/A')
            if address == 'N/A':
                parts = [loc.get('BuildingNumber', ''), loc.get('StreetName', ''),
                         loc.get('TownCity', ''), loc.get('County', ''),
                         loc.get('PostCode', '')]
                address = ', '.join(p for p in parts if p) or 'N/A'
            prop_info.append(["Address", address])

            prop_type = attrs.get('PropertyClassification', attrs.get('PropertyType', 'N/A'))
            prop_info.append(["Property Type", prop_type])

            if val.get('CurrentValue'):
                prop_info.append(["Current Value", f"£{val['CurrentValue']:,.2f}"])

            elev = risk.get('GroundLevelMeters')
            if elev:
                prop_info.append(["Ground Elevation", f"{elev:.2f} m AOD"])

            flood_zone = risk.get('FloodZone', 'N/A')
            prop_info.append(["Flood Zone", flood_zone])

            prop_table = Table(prop_info, colWidths=self.table_widths['two_col'])
            prop_table.setStyle(self.table_styles['standard'])
            elements.append(prop_table)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating mortgage title: {str(e)}",
                self.styles['Normal']
            ))

        return elements
