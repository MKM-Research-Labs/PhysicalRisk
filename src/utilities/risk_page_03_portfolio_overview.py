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

# src/utilities/flood_risk_page_03_portfolio_overview.py

"""
Page 3: Portfolio Overview
Handles the portfolio overview with methodology and gauge information.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from risk_base_page import FloodRiskBasePage


class FloodRiskPortfolioOverviewPage(FloodRiskBasePage):
    """Generates the portfolio overview page."""
    
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate portfolio overview elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Portfolio Overview", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # METHODOLOGY SECTION
            elements.append(Paragraph("Flood Analysis Methodology", self.styles['SectionHeader']))
            
            gauge_data = flood_data.get('gauge_data', {})
            gauge_count = len(gauge_data)
            
            methodology_text = f"""
            This analysis utilizes {gauge_count:,} flood gauges strategically positioned along the Thames to assess 
            flood risk. The model employs advanced spatial interpolation techniques to calculate property-specific flood 
            depths based on gauge readings and property elevations. Risk assessments incorporate depth-damage functions 
            calibrated for UK residential properties.
            """
            
            elements.append(Paragraph(methodology_text, self.styles['Normal']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # GAUGE INFORMATION SECTION
            if gauge_data:
                elements.append(Paragraph("Flood Gauge Network", self.styles['SectionHeader']))
                
                # Gauge statistics
                gauge_stats = self._calculate_gauge_statistics(gauge_data)
                
                stats_text = f"""
                The flood gauge network consists of {gauge_count:,} monitoring stations with an average elevation of 
                {gauge_stats['avg_elevation']:.1f}m. Gauges monitor water levels ranging from {gauge_stats['min_severe_level']:.1f}m 
                to {gauge_stats['max_max_level']:.1f}m, providing comprehensive coverage of potential flood scenarios.
                """
                
                elements.append(Paragraph(stats_text, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['minor_section']))
                
                # Sample gauge data table
                elements.append(Paragraph("Sample Gauge Information", self.styles['SubSectionHeader']))
                
                gauge_table_data = [['Gauge Name', 'Elevation (m)', 'Max Level (m)', 'Severe Level (m)', 'Flood Depth (m)']]
                
                # Add first 8 gauges as examples
                sample_gauges = list(gauge_data.items())[:8]
                for gauge_id, gauge_info in sample_gauges:
                    name = gauge_info.get('gauge_name', f'Gauge {gauge_id}')
                    elevation = gauge_info.get('elevation', 0)
                    max_level = gauge_info.get('max_level', 0)
                    severe_level = gauge_info.get('severe_level', 0)
                    flood_depth = max_level - severe_level if max_level and severe_level else 0
                    
                    gauge_table_data.append([
                        name[:25],  # Truncate long names
                        f"{elevation:.1f}" if elevation else "N/A",
                        f"{max_level:.1f}" if max_level else "N/A",
                        f"{severe_level:.1f}" if severe_level else "N/A",
                        f"{flood_depth:.1f}" if flood_depth > 0 else "0.0"
                    ])
                
                gauge_table = Table(gauge_table_data, colWidths=self.table_widths['five_col'])
                gauge_table.setStyle(self.table_styles['standard'])
                elements.append(gauge_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # PORTFOLIO CHARACTERISTICS SECTION
            elements.append(Paragraph("Portfolio Characteristics", self.styles['SectionHeader']))
            
            property_risk = flood_data.get('property_risk', {})
            portfolio_stats = self._calculate_portfolio_statistics(property_risk)
            
            # Property value distribution
            if portfolio_stats:
                char_text = f"""
                The property portfolio spans a diverse range of values, from {self._format_currency(portfolio_stats['min_value'])} 
                to {self._format_currency(portfolio_stats['max_value'])}, with an average property value of 
                {self._format_currency(portfolio_stats['avg_value'])}. Properties are distributed across various 
                flood risk zones, with {portfolio_stats['flooded_count']:,} properties experiencing some level of flood exposure.
                """
                
                elements.append(Paragraph(char_text, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['minor_section']))
                
                # Portfolio summary table
                portfolio_summary = [
                    ["Portfolio Metric", "Value"],
                    ["Total Properties", self._format_count(portfolio_stats['total_count'])],
                    ["Properties with Flood Exposure", self._format_count(portfolio_stats['flooded_count'])],
                    ["Average Property Value", self._format_currency(portfolio_stats['avg_value'])],
                    ["Median Property Value", self._format_currency(portfolio_stats['median_value'])],
                    ["Total Portfolio Value", self._format_currency(portfolio_stats['total_value'])],
                    ["Average Flood Depth (Exposed Properties)", self._format_depth(portfolio_stats['avg_flood_depth'])]
                ]
                
                portfolio_table = Table(portfolio_summary, colWidths=self.table_widths['two_col'])
                portfolio_table.setStyle(self.table_styles['property'])
                elements.append(portfolio_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # DATA QUALITY SECTION
            elements.append(Paragraph("Data Quality and Coverage", self.styles['SectionHeader']))
            
            quality_text = f"""
            This analysis incorporates data from {gauge_count:,} flood monitoring stations and 
            {len(property_risk):,} property assessments. All properties have been geo-located and assigned 
            flood risk levels based on proximity to monitoring gauges and terrain analysis. Data quality 
            checks ensure consistency and accuracy across all risk calculations.
            """
            
            elements.append(Paragraph(quality_text, self.styles['Normal']))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating portfolio overview: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _calculate_gauge_statistics(self, gauge_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate statistics for the gauge network."""
        elevations = []
        max_levels = []
        severe_levels = []
        
        for gauge_info in gauge_data.values():
            elevation = gauge_info.get('elevation', 0)
            max_level = gauge_info.get('max_level', 0)
            severe_level = gauge_info.get('severe_level', 0)
            
            if elevation:
                elevations.append(elevation)
            if max_level:
                max_levels.append(max_level)
            if severe_level:
                severe_levels.append(severe_level)
        
        return {
            'avg_elevation': sum(elevations) / len(elevations) if elevations else 0,
            'min_severe_level': min(severe_levels) if severe_levels else 0,
            'max_max_level': max(max_levels) if max_levels else 0
        }
    
    def _calculate_portfolio_statistics(self, property_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio statistics."""
        if not property_risk:
            return {}
        
        values = []
        flood_depths = []
        flooded_count = 0
        
        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            flood_depth = prop_data.get('flood_depth', 0) or 0
            
            values.append(prop_value)
            
            if flood_depth > 0:
                flood_depths.append(flood_depth)
                flooded_count += 1
        
        # Sort values for median calculation
        sorted_values = sorted(values)
        median_value = sorted_values[len(sorted_values) // 2] if sorted_values else 0
        
        return {
            'total_count': len(property_risk),
            'flooded_count': flooded_count,
            'min_value': min(values) if values else 0,
            'max_value': max(values) if values else 0,
            'avg_value': sum(values) / len(values) if values else 0,
            'median_value': median_value,
            'total_value': sum(values),
            'avg_flood_depth': sum(flood_depths) / len(flood_depths) if flood_depths else 0
        }