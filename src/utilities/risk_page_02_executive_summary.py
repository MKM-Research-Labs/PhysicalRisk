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

# src/utilities/flood_risk_page_02_executive_summary.py

"""
Page 2: Executive Summary
Handles the executive summary with key findings and risk analysis.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from risk_base_page import FloodRiskBasePage


class FloodRiskExecutiveSummaryPage(FloodRiskBasePage):
    """Generates the executive summary page."""
    
    def generate_elements(self, flood_data: Dict[str, Any]) -> List:
        """Generate executive summary elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Executive Summary", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            summary = flood_data.get('summary', {})
            
            # KEY FINDINGS SECTION
            elements.append(Paragraph("Key Findings", self.styles['SectionHeader']))
            
            # Generate findings text
            total_properties = summary.get('total_properties', 0)
            properties_at_risk = summary.get('properties_at_risk', 0)
            percentage_at_risk = summary.get('percentage_at_risk', 0)
            total_value = summary.get('total_value', 0)
            value_at_risk = summary.get('value_at_risk', 0)
            percentage_value_at_risk = summary.get('percentage_value_at_risk', 0)
            
            findings_text = f"""
            This flood risk analysis assesses {total_properties:,} properties with a combined value of 
            {self._format_currency(total_value)}. The analysis identifies {properties_at_risk:,} properties 
            ({self._format_percentage(percentage_at_risk)}) as being at medium to high flood risk, representing 
            {self._format_currency(value_at_risk)} ({self._format_percentage(percentage_value_at_risk)}) of the total portfolio value.
            """
            
            elements.append(Paragraph(findings_text, self.styles['Normal']))
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # RISK ANALYSIS SECTION
            elements.append(Paragraph("Risk Level Analysis", self.styles['SectionHeader']))
            
            property_risk = flood_data.get('property_risk', {})
            risk_analysis = self._analyze_risk_levels(property_risk)
            
            for risk_level, analysis in risk_analysis.items():
                if analysis['count'] > 0:
                    risk_text = f"""
                    {risk_level} Risk: {analysis['count']:,} properties ({analysis['percentage']:.1f}%) 
                    with an average flood depth of {analysis['avg_depth']:.2f}m and combined value at risk of 
                    {self._format_currency(analysis['total_value_at_risk'])}.
                    """
                    
                    # Use appropriate style based on risk level
                    style_name = f"{risk_level}Risk" if risk_level in ['High', 'Medium', 'Low'] else 'Normal'
                    style = self.styles.get(style_name, self.styles['Normal'])
                    elements.append(Paragraph(f"• {risk_text.strip()}", style))
            
            elements.append(Spacer(1, self.spacing['minor_section']))
            
            # MORTGAGE IMPACT SECTION (if available)
            mortgage_summary = summary.get('mortgage_summary', {})
            if mortgage_summary:
                elements.append(Paragraph("Mortgage Portfolio Impact", self.styles['SectionHeader']))
                
                total_mortgages = mortgage_summary.get('total_mortgages', 0)
                total_mortgage_value = mortgage_summary.get('total_mortgage_value', 0)
                mortgage_value_at_risk = mortgage_summary.get('mortgage_value_at_risk', 0)
                percentage_mortgage_value_at_risk = mortgage_summary.get('percentage_mortgage_value_at_risk', 0)
                
                mortgage_text = f"""
                The mortgage portfolio analysis reveals {total_mortgages:,} mortgages with a combined 
                value of {self._format_currency(total_mortgage_value)}. Flood risk exposure affects 
                {self._format_currency(mortgage_value_at_risk)} ({self._format_percentage(percentage_mortgage_value_at_risk)}) 
                of the mortgage portfolio value.
                """
                
                elements.append(Paragraph(mortgage_text, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['minor_section']))
                
                # Mortgage risk implications
                implications_text = """
                Key mortgage risk implications include:
                • Increased credit spreads reflecting higher default risk
                • Reduced collateral values in severe flood scenarios
                • Higher insurance costs and potential coverage gaps
                • Regulatory scrutiny under climate risk frameworks
                • Portfolio concentration risk in flood-prone areas
                """
                
                elements.append(Paragraph(implications_text, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['minor_section']))
            
            # RECOMMENDATIONS SECTION
            elements.append(Paragraph("Key Recommendations", self.styles['SectionHeader']))
            
            recommendations = self._generate_recommendations(risk_analysis, mortgage_summary)
            
            for recommendation in recommendations:
                elements.append(Paragraph(f"• {recommendation}", self.styles['Normal']))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating executive summary: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _analyze_risk_levels(self, property_risk: Dict[str, Any]) -> Dict[str, Dict]:
        """Analyze risk levels and calculate statistics."""
        risk_analysis = {
            "High": {"count": 0, "total_depth": 0, "total_value_at_risk": 0},
            "Medium": {"count": 0, "total_depth": 0, "total_value_at_risk": 0},
            "Low": {"count": 0, "total_depth": 0, "total_value_at_risk": 0},
            "Minimal": {"count": 0, "total_depth": 0, "total_value_at_risk": 0}
        }
        
        total_properties = len(property_risk)
        
        for prop_data in property_risk.values():
            risk_level = prop_data.get('risk_level', 'Unknown')
            if risk_level in risk_analysis:
                risk_analysis[risk_level]["count"] += 1
                risk_analysis[risk_level]["total_depth"] += prop_data.get('flood_depth', 0) or 0
                risk_analysis[risk_level]["total_value_at_risk"] += prop_data.get('value_at_risk', 0) or 0
        
        # Calculate averages and percentages
        for risk_level, data in risk_analysis.items():
            count = data["count"]
            data["percentage"] = (count / total_properties * 100) if total_properties > 0 else 0
            data["avg_depth"] = (data["total_depth"] / count) if count > 0 else 0
        
        return risk_analysis
    
    def _generate_recommendations(self, risk_analysis: Dict, mortgage_summary: Dict) -> List[str]:
        """Generate recommendations based on risk analysis."""
        recommendations = []
        
        # High risk recommendations
        if risk_analysis["High"]["count"] > 0:
            recommendations.append(
                f"Immediate attention required for {risk_analysis['High']['count']:,} high-risk properties. "
                "Consider flood protection measures and detailed property assessments."
            )
        
        # Medium risk recommendations
        if risk_analysis["Medium"]["count"] > 0:
            recommendations.append(
                f"Monitor {risk_analysis['Medium']['count']:,} medium-risk properties for changing conditions. "
                "Implement early warning systems and review insurance coverage."
            )
        
        # Portfolio diversification
        total_at_risk = risk_analysis["High"]["count"] + risk_analysis["Medium"]["count"]
        if total_at_risk > 0:
            recommendations.append(
                "Consider portfolio diversification to reduce geographic concentration of flood risk."
            )
        
        # Mortgage-specific recommendations
        if mortgage_summary:
            recommendations.append(
                "Review loan-to-value ratios for flood-exposed properties and consider climate risk in underwriting."
            )
        
        # General recommendations
        recommendations.extend([
            "Establish regular flood risk monitoring and reporting procedures.",
            "Engage with local flood defense authorities and community resilience initiatives.",
            "Consider climate-resilient property improvements and green infrastructure investments."
        ])
        
        return recommendations