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

# src/utilities/flood_risk_page_01_title.py

"""
Page 1: Title and Portfolio Overview
Handles the title page with basic portfolio information and key metrics.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from risk_base_page import FloodRiskBasePage


class FloodRiskTitlePage(FloodRiskBasePage):
    """Generates the title page with portfolio overview."""
    
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate title page elements."""
        elements = []
        
        try:
            # TITLE SECTION
            elements.append(Paragraph(
                "Flood Risk Analysis Report", 
                self.styles['Title']
            ))
            elements.append(Spacer(1, 0.3*inch))
            
            # Extract summary data
            summary = flood_data.get('summary', {})
            total_properties = summary.get('total_properties', 0)
            
            elements.append(Paragraph(
                f"Portfolio Assessment: {total_properties:,} Properties", 
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                f"Report Date: {datetime.now().strftime('%B %d, %Y')}", 
                self.styles['Normal']
            ))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # KEY METRICS SECTION
            elements.append(Paragraph("Portfolio Summary", self.styles['SectionHeader']))
            
            # Create key metrics table
            key_metrics = [["Metric", "Value"]]
            
            # Core metrics
            key_metrics.extend([
                ["Total Properties", self._format_count(summary.get('total_properties', 0))],
                ["Properties at Risk", f"{self._format_count(summary.get('properties_at_risk', 0))} ({self._format_percentage(summary.get('percentage_at_risk', 0))})"],
                ["Total Property Value", self._format_currency(summary.get('total_value', 0))],
                ["Value at Risk", self._format_currency(summary.get('value_at_risk', 0))],
                ["Percentage Value at Risk", self._format_percentage(summary.get('percentage_value_at_risk', 0))]
            ])
            
            # Add mortgage metrics if available
            mortgage_summary = summary.get('mortgage_summary', {})
            if mortgage_summary:
                key_metrics.extend([
                    ["Total Mortgages", self._format_count(mortgage_summary.get('total_mortgages', 0))],
                    ["Mortgage Value at Risk", self._format_currency(mortgage_summary.get('mortgage_value_at_risk', 0))],
                    ["Mortgages at Risk", f"{self._format_count(mortgage_summary.get('mortgages_at_risk_count', 0))} ({self._format_percentage(mortgage_summary.get('percentage_mortgages_at_risk', 0))})"]
                ])
            
            table = Table(key_metrics, colWidths=self.table_widths['two_col'])
            table.setStyle(self.table_styles['standard'])
            elements.append(table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RISK LEVEL OVERVIEW
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Risk Level Distribution", self.styles['SectionHeader']))
            
            # Calculate risk distribution
            property_risk = flood_data.get('property_risk', {})
            risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Minimal": 0, "Unknown": 0}
            
            for prop_data in property_risk.values():
                risk_level = prop_data.get('risk_level', 'Unknown')
                if risk_level in risk_counts:
                    risk_counts[risk_level] += 1
                else:
                    risk_counts['Unknown'] += 1
            
            # Create risk distribution table
            risk_data = [["Risk Level", "Properties", "Percentage"]]
            total_props = len(property_risk) if property_risk else 1
            
            for risk_level, count in risk_counts.items():
                if count > 0:
                    percentage = (count / total_props) * 100
                    risk_data.append([
                        risk_level,
                        self._format_count(count),
                        self._format_percentage(percentage)
                    ])
            
            risk_table = Table(risk_data, colWidths=self.table_widths['three_col'])
            risk_table.setStyle(self.table_styles['risk_summary'])
            elements.append(risk_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # REPORT METADATA
            elements.append(Spacer(1, self.spacing['major_section']))
            elements.append(Paragraph("Report Information", self.styles['SectionHeader']))
            
            # Extract timestamp
            timestamp = flood_data.get('timestamp', datetime.now().isoformat())
            try:
                report_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y at %H:%M')
            except:
                report_date = datetime.now().strftime('%B %d, %Y at %H:%M')
            
            metadata = [
                ["Analysis Date", report_date],
                ["Report Generator", "MKM Research Labs"],
                ["Analysis Type", "Comprehensive Flood Risk Assessment"],
                ["Data Sources", f"{len(flood_data.get('gauge_data', {})):,} flood gauges"]
            ]
            
            metadata_table = Table(metadata, colWidths=self.table_widths['two_col'])
            metadata_table.setStyle(self.table_styles['standard'])
            elements.append(metadata_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating title page: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements