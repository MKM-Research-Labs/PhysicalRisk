# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# src/utilities/flood_risk_page_05_mortgage_analysis.py

"""
Page 5: Mortgage Risk Analysis
Handles mortgage-specific flood risk analysis and financial implications.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from risk_base_page import FloodRiskBasePage


class FloodRiskMortgageAnalysisPage(FloodRiskBasePage):
    """Generates the mortgage risk analysis page."""
    
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate mortgage risk analysis elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Mortgage Risk Analysis", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            summary = flood_data.get('summary', {})
            mortgage_summary = summary.get('mortgage_summary', {})
            
            if not mortgage_summary:
                elements.append(Paragraph(
                    "Mortgage analysis data not available for this portfolio.", 
                    self.styles['Normal']
                ))
                return elements
            
            # MORTGAGE PORTFOLIO OVERVIEW
            elements.append(Paragraph("Mortgage Portfolio Overview", self.styles['SectionHeader']))
            
            total_mortgages = mortgage_summary.get('total_mortgages', 0)
            total_mortgage_value = mortgage_summary.get('total_mortgage_value', 0)
            mortgage_value_at_risk = mortgage_summary.get('mortgage_value_at_risk', 0)
            percentage_mortgage_value_at_risk = mortgage_summary.get('percentage_mortgage_value_at_risk', 0)
            
            overview_text = f"""
            The mortgage portfolio consists of {total_mortgages:,} loans with a combined value of 
            {self._format_currency(total_mortgage_value)}. Flood risk exposure affects 
            {self._format_currency(mortgage_value_at_risk)} ({self._format_percentage(percentage_mortgage_value_at_risk)}) 
            of the total mortgage portfolio value.
            """
            
            elements.append(Paragraph(overview_text, self.styles['Normal']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # MORTGAGE RISK METRICS
            mortgage_metrics = [
                ["Mortgage Risk Metric", "Value"],
                ["Total Mortgages", self._format_count(total_mortgages)],
                ["Total Mortgage Value", self._format_currency(total_mortgage_value)],
                ["Mortgages at Risk", f"{self._format_count(mortgage_summary.get('mortgages_at_risk_count', 0))} ({self._format_percentage(mortgage_summary.get('percentage_mortgages_at_risk', 0))})"],
                ["Mortgage Value at Risk", self._format_currency(mortgage_value_at_risk)],
                ["Percentage Value at Risk", self._format_percentage(percentage_mortgage_value_at_risk)]
            ]
            
            mortgage_table = Table(mortgage_metrics, colWidths=self.table_widths['two_col'])
            mortgage_table.setStyle(self.table_styles['risk_summary'])
            elements.append(mortgage_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RISK IMPLICATIONS
            elements.append(Paragraph("Risk Implications", self.styles['SectionHeader']))
            
            implications_text = """
            Flood-exposed mortgages may experience:
            
            - Increased credit spreads reflecting higher default risk
            - Reduced collateral values in severe flood scenarios  
            - Higher insurance costs and potential coverage gaps
            - Regulatory scrutiny under climate risk frameworks
            - Portfolio concentration risk in flood-prone areas
            """
            
            elements.append(Paragraph(implications_text, self.styles['Normal']))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating mortgage analysis: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements