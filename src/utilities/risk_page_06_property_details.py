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

# src/utilities/flood_risk_page_06_property_details.py

"""
Page 6: Property Risk Details  
Handles detailed property-level risk information and analysis.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from risk_base_page import FloodRiskBasePage


class FloodRiskPropertyDetailsPage(FloodRiskBasePage):
    """Generates the property risk details page."""
    
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate property risk details elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Property Risk Details", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            property_risk = flood_data.get('property_risk', {})
            
            # PROPERTIES AT RISK OVERVIEW
            at_risk_properties = [prop for prop in property_risk.values() 
                                if prop.get('risk_level') in ['High', 'Medium']]
            
            if at_risk_properties:
                elements.append(Paragraph(
                    f"Properties at Risk ({len(at_risk_properties):,} properties)", 
                    self.styles['SectionHeader']
                ))
                
                # Sort by risk value
                sorted_properties = sorted(at_risk_properties, 
                                         key=lambda x: x.get('risk_value', 0), reverse=True)
                
                # Create comprehensive property table
                prop_data = [['Property ID', 'Risk Level', 'Elevation (m)', 'Flood Depth (m)', 'Property Value (£)', 'Value at Risk (£)']]
                
                # Show top 20 properties at risk
                display_count = min(20, len(sorted_properties))
                for prop in sorted_properties[:display_count]:
                    prop_id = prop.get('property_id', 'Unknown')
                    risk_level = prop.get('risk_level', 'Unknown')
                    elevation = prop.get('elevation', 0)
                    flood_depth = prop.get('flood_depth', 0)
                    prop_value = prop.get('property_value', 0)
                    value_at_risk = prop.get('value_at_risk', 0)
                    
                    prop_data.append([
                        str(prop_id)[:15],
                        risk_level,
                        f"{elevation:.1f}" if elevation else "N/A",
                        self._format_depth(flood_depth),
                        self._format_currency(prop_value),
                        self._format_currency(value_at_risk)
                    ])
                
                prop_table = Table(prop_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 1*inch, 1.5*inch, 1.5*inch])
                prop_table.setStyle(self.table_styles['property'])
                elements.append(prop_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
                
                if len(at_risk_properties) > display_count:
                    elements.append(Paragraph(
                        f"Note: Showing top {display_count} of {len(at_risk_properties):,} properties at risk.", 
                        self.styles['Normal']
                    ))
                    elements.append(Spacer(1, self.spacing['minor_section']))
            
            # PROPERTY VALUE ANALYSIS
            elements.append(Paragraph("Property Value Analysis", self.styles['SectionHeader']))
            
            value_analysis = self._analyze_property_values(property_risk)
            
            value_text = f"""
            The property portfolio spans values from {self._format_currency(value_analysis['min_value'])} 
            to {self._format_currency(value_analysis['max_value'])}. Properties at risk have an average value of 
            {self._format_currency(value_analysis['avg_at_risk_value'])}, compared to the portfolio average of 
            {self._format_currency(value_analysis['portfolio_avg_value'])}.
            """
            
            elements.append(Paragraph(value_text, self.styles['Normal']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # Value distribution table
            value_ranges = self._categorize_property_values(property_risk)
            value_data = [["Property Value Range", "Total Properties", "At Risk", "Risk %", "Total Value at Risk"]]
            
            for value_range, data in value_ranges.items():
                if data['total_count'] > 0:
                    risk_percentage = (data['at_risk_count'] / data['total_count'] * 100) if data['total_count'] > 0 else 0
                    value_data.append([
                        value_range,
                        self._format_count(data['total_count']),
                        self._format_count(data['at_risk_count']),
                        self._format_percentage(risk_percentage),
                        self._format_currency(data['total_value_at_risk'])
                    ])
            
            value_table = Table(value_data, colWidths=self.table_widths['five_col'])
            value_table.setStyle(self.table_styles['standard'])
            elements.append(value_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # GEOGRAPHIC RISK DISTRIBUTION
            elements.append(Paragraph("Geographic Risk Distribution", self.styles['SectionHeader']))
            
            risk_distribution = self._analyze_risk_distribution(property_risk)
            
            distribution_text = f"""
            Risk analysis reveals {risk_distribution['high_risk_percentage']:.1f}% of high-value properties 
            (above £1M) are at flood risk, while {risk_distribution['low_risk_percentage']:.1f}% of lower-value 
            properties face similar exposure. This indicates varying degrees of geographic risk concentration 
            across different property value segments.
            """
            
            elements.append(Paragraph(distribution_text, self.styles['Normal']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # Risk by value segment table
            segment_data = [["Value Segment", "Properties", "At Risk", "Risk %", "Avg Flood Depth (m)"]]
            
            for segment, data in risk_distribution['segments'].items():
                if data['total'] > 0:
                    risk_pct = (data['at_risk'] / data['total'] * 100) if data['total'] > 0 else 0
                    segment_data.append([
                        segment,
                        self._format_count(data['total']),
                        self._format_count(data['at_risk']),
                        self._format_percentage(risk_pct),
                        self._format_depth(data['avg_depth'])
                    ])
            
            segment_table = Table(segment_data, colWidths=self.table_widths['five_col'])
            segment_table.setStyle(self.table_styles['risk_summary'])
            elements.append(segment_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # PORTFOLIO IMPACT SUMMARY
            elements.append(Paragraph("Portfolio Impact Summary", self.styles['SectionHeader']))
            
            portfolio_impact = self._calculate_portfolio_impact(property_risk)
            
            impact_summary_data = [
                ["Impact Metric", "Value"],
                ["Total Properties Analyzed", self._format_count(portfolio_impact['total_properties'])],
                ["Properties with Flood Risk", self._format_count(portfolio_impact['properties_at_risk'])],
                ["Portfolio Risk Percentage", self._format_percentage(portfolio_impact['portfolio_risk_percentage'])],
                ["Total Portfolio Value", self._format_currency(portfolio_impact['total_portfolio_value'])],
                ["Total Value at Risk", self._format_currency(portfolio_impact['total_value_at_risk'])],
                ["Value Risk Percentage", self._format_percentage(portfolio_impact['value_risk_percentage'])],
                ["Average Risk per Property", self._format_currency(portfolio_impact['avg_risk_per_property'])]
            ]
            
            impact_table = Table(impact_summary_data, colWidths=self.table_widths['two_col'])
            impact_table.setStyle(self.table_styles['standard'])
            elements.append(impact_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating property details: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _analyze_property_values(self, property_risk: Dict[str, Any]) -> Dict[str, float]:
        """Analyze property values across the portfolio."""
        all_values = []
        at_risk_values = []
        
        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            risk_level = prop_data.get('risk_level', 'Unknown')
            
            all_values.append(prop_value)
            if risk_level in ['High', 'Medium']:
                at_risk_values.append(prop_value)
        
        return {
            'min_value': min(all_values) if all_values else 0,
            'max_value': max(all_values) if all_values else 0,
            'portfolio_avg_value': sum(all_values) / len(all_values) if all_values else 0,
            'avg_at_risk_value': sum(at_risk_values) / len(at_risk_values) if at_risk_values else 0
        }
    
    def _categorize_property_values(self, property_risk: Dict[str, Any]) -> Dict[str, Dict]:
        """Categorize properties by value ranges."""
        categories = {
            "Under £500K": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "£500K-£1M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "£1M-£2M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "£2M-£5M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0},
            "Over £5M": {"total_count": 0, "at_risk_count": 0, "total_value_at_risk": 0}
        }
        
        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            risk_level = prop_data.get('risk_level', 'Unknown')
            value_at_risk = prop_data.get('value_at_risk', 0) or 0
            
            # Determine value category
            if prop_value < 500000:
                category = "Under £500K"
            elif prop_value < 1000000:
                category = "£500K-£1M"
            elif prop_value < 2000000:
                category = "£1M-£2M"
            elif prop_value < 5000000:
                category = "£2M-£5M"
            else:
                category = "Over £5M"
            
            categories[category]["total_count"] += 1
            if risk_level in ['High', 'Medium']:
                categories[category]["at_risk_count"] += 1
                categories[category]["total_value_at_risk"] += value_at_risk
        
        return categories
    
    def _analyze_risk_distribution(self, property_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk distribution across property segments."""
        segments = {
            "High Value (>£1M)": {"total": 0, "at_risk": 0, "total_depth": 0},
            "Medium Value (£500K-£1M)": {"total": 0, "at_risk": 0, "total_depth": 0},
            "Lower Value (<£500K)": {"total": 0, "at_risk": 0, "total_depth": 0}
        }
        
        high_value_at_risk = 0
        high_value_total = 0
        low_value_at_risk = 0
        low_value_total = 0
        
        for prop_data in property_risk.values():
            prop_value = prop_data.get('property_value', 0) or 0
            risk_level = prop_data.get('risk_level', 'Unknown')
            flood_depth = prop_data.get('flood_depth', 0) or 0
            
            # Determine segment
            if prop_value >= 1000000:
                segment = "High Value (>£1M)"
                high_value_total += 1
                if risk_level in ['High', 'Medium']:
                    high_value_at_risk += 1
            elif prop_value >= 500000:
                segment = "Medium Value (£500K-£1M)"
            else:
                segment = "Lower Value (<£500K)"
                low_value_total += 1
                if risk_level in ['High', 'Medium']:
                    low_value_at_risk += 1
            
            segments[segment]["total"] += 1
            if risk_level in ['High', 'Medium']:
                segments[segment]["at_risk"] += 1
                segments[segment]["total_depth"] += flood_depth
        
        # Calculate average depths
        for segment_data in segments.values():
            at_risk_count = segment_data["at_risk"]
            segment_data["avg_depth"] = (
                segment_data["total_depth"] / at_risk_count if at_risk_count > 0 else 0
            )
        
        return {
            'segments': segments,
            'high_risk_percentage': (high_value_at_risk / high_value_total * 100) if high_value_total > 0 else 0,
            'low_risk_percentage': (low_value_at_risk / low_value_total * 100) if low_value_total > 0 else 0
        }
    
    def _calculate_portfolio_impact(self, property_risk: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall portfolio impact metrics."""
        total_properties = len(property_risk)
        properties_at_risk = 0
        total_portfolio_value = 0
        total_value_at_risk = 0
        
        for prop_data in property_risk.values():
            risk_level = prop_data.get('risk_level', 'Unknown')
            prop_value = prop_data.get('property_value', 0) or 0
            value_at_risk = prop_data.get('value_at_risk', 0) or 0
            
            total_portfolio_value += prop_value
            total_value_at_risk += value_at_risk
            
            if risk_level in ['High', 'Medium']:
                properties_at_risk += 1
        
        return {
            'total_properties': total_properties,
            'properties_at_risk': properties_at_risk,
            'portfolio_risk_percentage': (properties_at_risk / total_properties * 100) if total_properties > 0 else 0,
            'total_portfolio_value': total_portfolio_value,
            'total_value_at_risk': total_value_at_risk,
            'value_risk_percentage': (total_value_at_risk / total_portfolio_value * 100) if total_portfolio_value > 0 else 0,
            'avg_risk_per_property': total_value_at_risk / total_properties if total_properties > 0 else 0
        }