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

# src/utilities/flood_risk_page_04_risk_analysis.py

"""
Page 4: Detailed Risk Analysis
Handles detailed flood risk analysis with property-level breakdowns.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from risk_base_page import FloodRiskBasePage


class FloodRiskAnalysisPage(FloodRiskBasePage):
    """Generates the detailed risk analysis page."""
    
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate detailed risk analysis elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Detailed Risk Analysis", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            property_risk = flood_data.get('property_risk', {})
            
            # HIGH RISK PROPERTIES SECTION
            high_risk_properties = self._filter_properties_by_risk(property_risk, "High")
            
            if high_risk_properties:
                elements.append(Paragraph("High Risk Properties", self.styles['SectionHeader']))
                
                high_risk_text = f"""
                {len(high_risk_properties):,} properties are classified as high risk, with flood depths exceeding 1 meter 
                and damage ratios above 60%. These properties require immediate attention and may benefit from flood 
                protection measures.
                """
                elements.append(Paragraph(high_risk_text, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['minor_section']))
                
                # High risk table
                high_risk_data = [['Property ID', 'Flood Depth (m)', 'Risk Value (%)', 'Property Value (£)', 'Value at Risk (£)']]
                
                # Sort by risk value and show top 15
                sorted_high_risk = sorted(high_risk_properties, 
                                        key=lambda x: x.get('risk_value', 0), reverse=True)[:15]
                
                for prop in sorted_high_risk:
                    prop_id = prop.get('property_id', 'Unknown')
                    flood_depth = prop.get('flood_depth', 0)
                    risk_value = prop.get('risk_value', 0)
                    prop_value = prop.get('property_value', 0)
                    value_at_risk = prop.get('value_at_risk', 0)
                    
                    high_risk_data.append([
                        str(prop_id)[:15],
                        self._format_depth(flood_depth),
                        f"{risk_value*100:.1f}" if risk_value else "0.0",
                        self._format_currency(prop_value),
                        self._format_currency(value_at_risk)
                    ])
                
                high_risk_table = Table(high_risk_data, colWidths=self.table_widths['five_col'])
                high_risk_table.setStyle(self.table_styles['risk_summary'])
                elements.append(high_risk_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
                
                if len(high_risk_properties) > 15:
                    elements.append(Paragraph(
                        f"Note: Showing top 15 of {len(high_risk_properties):,} high-risk properties.", 
                        self.styles['Normal']
                    ))
                    elements.append(Spacer(1, self.spacing['minor_section']))
            
            # MEDIUM RISK PROPERTIES SECTION
            medium_risk_properties = self._filter_properties_by_risk(property_risk, "Medium")
            
            if medium_risk_properties:
                elements.append(Paragraph("Medium Risk Properties", self.styles['SectionHeader']))
                
                medium_risk_text = f"""
                {len(medium_risk_properties):,} properties are classified as medium risk, with moderate flood exposure 
                requiring monitoring and potential mitigation measures. These properties should be regularly assessed 
                for changing risk conditions.
                """
                elements.append(Paragraph(medium_risk_text, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['minor_section']))
                
                # Medium risk summary table
                medium_stats = self._calculate_risk_statistics(medium_risk_properties)
                medium_summary_data = [
                    ["Medium Risk Summary", "Value"],
                    ["Total Properties", self._format_count(medium_stats['count'])],
                    ["Average Flood Depth", self._format_depth(medium_stats['avg_depth'])],
                    ["Total Value at Risk", self._format_currency(medium_stats['total_value_at_risk'])],
                    ["Average Property Value", self._format_currency(medium_stats['avg_property_value'])]
                ]
                
                medium_summary_table = Table(medium_summary_data, colWidths=self.table_widths['two_col'])
                medium_summary_table.setStyle(self.table_styles['standard'])
                elements.append(medium_summary_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FLOOD DEPTH ANALYSIS SECTION
            elements.append(Paragraph("Flood Depth Analysis", self.styles['SectionHeader']))
            
            depth_analysis = self._analyze_flood_depths(property_risk)
            
            depth_text = f"""
            Flood depth analysis reveals {depth_analysis['flooded_properties']:,} properties with flood exposure. 
            The average flood depth across affected properties is {depth_analysis['avg_depth']:.2f}m, with the 
            maximum depth reaching {depth_analysis['max_depth']:.2f}m. Properties with depths exceeding 2 meters 
            ({depth_analysis['severe_depth_count']:,} properties) face the highest risk of structural damage.
            """
            
            elements.append(Paragraph(depth_text, self.styles['Normal']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # Depth distribution table
            depth_ranges = self._categorize_flood_depths(property_risk)
            depth_data = [["Flood Depth Range", "Properties", "Percentage", "Avg Damage Ratio"]]
            
            total_flooded = sum(data['count'] for data in depth_ranges.values())
            
            for depth_range, data in depth_ranges.items():
                if data['count'] > 0:
                    percentage = (data['count'] / total_flooded * 100) if total_flooded > 0 else 0
                    depth_data.append([
                        depth_range,
                        self._format_count(data['count']),
                        self._format_percentage(percentage),
                        self._format_percentage(data['avg_damage_ratio'] * 100)
                    ])
            
            depth_table = Table(depth_data, colWidths=self.table_widths['four_col'])
            depth_table.setStyle(self.table_styles['standard'])
            elements.append(depth_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RISK MITIGATION RECOMMENDATIONS
            elements.append(Paragraph("Risk Mitigation Recommendations", self.styles['SectionHeader']))
            
            recommendations = self._generate_mitigation_recommendations(
                high_risk_properties, medium_risk_properties, depth_analysis
            )
            
            for recommendation in recommendations:
                elements.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating risk analysis: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _filter_properties_by_risk(self, property_risk: Dict[str, Any], risk_level: str) -> List[Dict]:
        """Filter properties by risk level."""
        return [prop_data for prop_data in property_risk.values() 
                if prop_data.get('risk_level') == risk_level]
    
    def _calculate_risk_statistics(self, properties: List[Dict]) -> Dict[str, float]:
        """Calculate statistics for a group of properties."""
        if not properties:
            return {'count': 0, 'avg_depth': 0, 'total_value_at_risk': 0, 'avg_property_value': 0}
        
        total_depth = sum(prop.get('flood_depth', 0) or 0 for prop in properties)
        total_value_at_risk = sum(prop.get('value_at_risk', 0) or 0 for prop in properties)
        total_property_value = sum(prop.get('property_value', 0) or 0 for prop in properties)
        
        return {
            'count': len(properties),
            'avg_depth': total_depth / len(properties),
            'total_value_at_risk': total_value_at_risk,
            'avg_property_value': total_property_value / len(properties)
        }
    
    def _analyze_flood_depths(self, property_risk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze flood depths across all properties."""
        flood_depths = []
        flooded_properties = 0
        severe_depth_count = 0
        
        for prop_data in property_risk.values():
            depth = prop_data.get('flood_depth', 0) or 0
            if depth > 0:
                flood_depths.append(depth)
                flooded_properties += 1
                if depth > 2.0:
                    severe_depth_count += 1
        
        return {
            'flooded_properties': flooded_properties,
            'avg_depth': sum(flood_depths) / len(flood_depths) if flood_depths else 0,
            'max_depth': max(flood_depths) if flood_depths else 0,
            'severe_depth_count': severe_depth_count
        }
    
    def _categorize_flood_depths(self, property_risk: Dict[str, Any]) -> Dict[str, Dict]:
        """Categorize properties by flood depth ranges."""
        categories = {
            "0-0.5m": {"count": 0, "total_damage_ratio": 0},
            "0.5-1.0m": {"count": 0, "total_damage_ratio": 0},
            "1.0-2.0m": {"count": 0, "total_damage_ratio": 0},
            "2.0m+": {"count": 0, "total_damage_ratio": 0}
        }
        
        for prop_data in property_risk.values():
            depth = prop_data.get('flood_depth', 0) or 0
            risk_value = prop_data.get('risk_value', 0) or 0
            
            if depth > 0:
                if depth <= 0.5:
                    category = "0-0.5m"
                elif depth <= 1.0:
                    category = "0.5-1.0m"
                elif depth <= 2.0:
                    category = "1.0-2.0m"
                else:
                    category = "2.0m+"
                
                categories[category]["count"] += 1
                categories[category]["total_damage_ratio"] += risk_value
        
        # Calculate average damage ratios
        for category_data in categories.values():
            count = category_data["count"]
            category_data["avg_damage_ratio"] = (
                category_data["total_damage_ratio"] / count if count > 0 else 0
            )
        
        return categories
    
    def _generate_mitigation_recommendations(self, high_risk: List, medium_risk: List, 
                                           depth_analysis: Dict) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if high_risk:
            recommendations.extend([
                f"Prioritize flood defenses for {len(high_risk):,} high-risk properties, including barriers and drainage improvements.",
                "Conduct detailed structural assessments for properties with flood depths exceeding 1 meter.",
                "Consider property-level resilience measures such as flood doors and elevated utilities."
            ])
        
        if medium_risk:
            recommendations.extend([
                f"Implement monitoring systems for {len(medium_risk):,} medium-risk properties.",
                "Review and update flood insurance coverage for medium-risk properties."
            ])
        
        if depth_analysis['severe_depth_count'] > 0:
            recommendations.append(
                f"Urgent intervention required for {depth_analysis['severe_depth_count']:,} properties "
                "with flood depths exceeding 2 meters."
            )
        
        recommendations.extend([
            "Establish early warning systems linked to gauge network monitoring.",
            "Develop evacuation and emergency response plans for high-risk areas.",
            "Consider strategic property acquisition in the highest-risk zones.",
            "Invest in community-level flood defense infrastructure."
        ])
        
        return recommendations