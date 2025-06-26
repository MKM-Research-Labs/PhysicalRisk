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

# src/utilities/page_07_protection.py

"""
Page 7: Protection Measures
Handles flood protection, resilience measures, and risk mitigation systems.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class ProtectionPage(BasePage):
    """Generates protection measures page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate protection measures page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Protection Measures", self.styles['SectionHeader']))
            
            protection_data = property_data.get('ProtectionMeasures', {})
            
            if not protection_data:
                elements.append(Paragraph("No protection measures data available.", self.styles['Normal']))
                return elements
            
            # INSURANCE & RISK ASSESSMENT
            risk_assessment = protection_data.get('RiskAssessment', {})
            if risk_assessment:
                elements.append(Paragraph("Insurance & Risk Assessment", self.styles['SubSectionHeader']))
                
                insurance_data = [["Insurance Factor", "Details"]]
                
                # Insurance premium and details
                premium = risk_assessment.get('InsurancePremium')
                if isinstance(premium, (int, float)):
                    insurance_data.append(["Annual Insurance Premium", self._format_currency(premium)])
                
                excess = risk_assessment.get('ExcessAmount')
                if isinstance(excess, (int, float)):
                    insurance_data.append(["Insurance Excess", self._format_currency(excess)])
                
                # Insurance status and eligibility
                for key, value in risk_assessment.items():
                    if key not in ['InsurancePremium', 'ExcessAmount'] and value is not None:
                        insurance_data.append([self._format_field_name(key), self._format_value(value)])
                
                insurance_table = Table(insurance_data, colWidths=self.table_widths['two_col'])
                insurance_table.setStyle(self.table_styles['financial'])
                elements.append(insurance_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RESILIENCE MEASURES
            resilience_measures = protection_data.get('ResilienceMeasures', {})
            if resilience_measures:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Resilience Measures", self.styles['SubSectionHeader']))
                
                # Calculate coverage statistics
                installed_count = sum(1 for value in resilience_measures.values() if value)
                total_count = len(resilience_measures)
                coverage_percentage = (installed_count / total_count * 100) if total_count > 0 else 0
                
                # Summary statistics
                summary_data = [["Protection Summary", "Status"]]
                summary_data.append(["Measures Installed", f"{installed_count} of {total_count}"])
                summary_data.append(["Coverage Percentage", f"{coverage_percentage:.1f}%"])
                
                # Coverage assessment
                if coverage_percentage >= 80:
                    coverage_rating = "Excellent - Comprehensive protection"
                elif coverage_percentage >= 60:
                    coverage_rating = "Good - Well protected"
                elif coverage_percentage >= 40:
                    coverage_rating = "Fair - Moderate protection"
                elif coverage_percentage >= 20:
                    coverage_rating = "Limited - Basic protection only"
                else:
                    coverage_rating = "Poor - Minimal protection"
                
                summary_data.append(["Protection Rating", coverage_rating])
                
                summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
                summary_table.setStyle(self.table_styles['protection'])
                elements.append(summary_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
                
                # Detailed measures list
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Installed Protection Measures", self.styles['SubSectionHeader']))
                
                measures_data = [["Protection Measure", "Status"]]
                
                # Group measures by category for better presentation
                critical_measures = ['FloodGates', 'FloodBarriers', 'SumpPump', 'NonReturnValves']
                building_measures = ['WaterproofFlooring', 'RaisedElectricals', 'WaterproofPlaster']
                emergency_measures = ['FloodWarningSystem', 'EmergencyKit', 'SandBags']
                
                # Show critical measures first
                for measure in critical_measures:
                    if measure in resilience_measures:
                        status = "✓ Installed" if resilience_measures[measure] else "✗ Not Installed"
                        measures_data.append([self._format_field_name(measure), status])
                
                # Then building measures
                for measure in building_measures:
                    if measure in resilience_measures:
                        status = "✓ Installed" if resilience_measures[measure] else "✗ Not Installed"
                        measures_data.append([self._format_field_name(measure), status])
                
                # Finally emergency measures
                for measure in emergency_measures:
                    if measure in resilience_measures:
                        status = "✓ Installed" if resilience_measures[measure] else "✗ Not Installed"
                        measures_data.append([self._format_field_name(measure), status])
                
                # Any remaining measures
                all_categorized = critical_measures + building_measures + emergency_measures
                for measure, value in resilience_measures.items():
                    if measure not in all_categorized:
                        status = "✓ Installed" if value else "✗ Not Installed"
                        measures_data.append([self._format_field_name(measure), status])
                
                measures_table = Table(measures_data, colWidths=self.table_widths['two_col'])
                measures_table.setStyle(self.table_styles['protection'])
                elements.append(measures_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # NATURAL PROTECTION MEASURES
            natural_measures = protection_data.get('NaturalMeasures', {})
            if natural_measures:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Natural Protection Measures", self.styles['SubSectionHeader']))
                
                natural_installed = sum(1 for value in natural_measures.values() if value)
                natural_total = len(natural_measures)
                natural_percentage = (natural_installed / natural_total * 100) if natural_total > 0 else 0
                
                natural_data = [["Natural Measure", "Status"]]
                natural_data.append(["Measures Implemented", f"{natural_installed} of {natural_total} ({natural_percentage:.1f}%)"])
                
                # List implemented measures
                for key, value in natural_measures.items():
                    status = "✓ Implemented" if value else "✗ Not Implemented"
                    natural_data.append([self._format_field_name(key), status])
                
                natural_table = Table(natural_data, colWidths=self.table_widths['two_col'])
                natural_table.setStyle(self.table_styles['protection'])
                elements.append(natural_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # PROTECTION RECOMMENDATIONS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Protection Recommendations", self.styles['SubSectionHeader']))
            
            recommendations = self._generate_protection_recommendations(protection_data)
            
            rec_data = [["Recommendation Category", "Suggested Actions"]]
            for category, actions in recommendations.items():
                rec_data.append([category, actions])
            
            rec_table = Table(rec_data, colWidths=self.table_widths['two_col'])
            rec_table.setStyle(self.table_styles['standard'])
            elements.append(rec_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating protection measures: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _generate_protection_recommendations(self, protection_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate protection recommendations based on current measures."""
        recommendations = {}
        
        resilience_measures = protection_data.get('ResilienceMeasures', {})
        natural_measures = protection_data.get('NaturalMeasures', {})
        
        # Check for missing critical measures
        missing_critical = []
        critical_measures = ['FloodGates', 'FloodBarriers', 'SumpPump', 'NonReturnValves']
        
        for measure in critical_measures:
            if not resilience_measures.get(measure, False):
                missing_critical.append(self._format_field_name(measure))
        
        if missing_critical:
            recommendations["Priority Installations"] = "Install: " + ", ".join(missing_critical)
        
        # Check natural measures
        if not any(natural_measures.values()):
            recommendations["Natural Solutions"] = "Consider implementing sustainable drainage solutions"
        
        # Insurance recommendations
        risk_assessment = protection_data.get('RiskAssessment', {})
        flood_re_eligible = risk_assessment.get('FloodReEligible')
        if flood_re_eligible:
            recommendations["Insurance"] = "Ensure Flood Re coverage is active for affordable premiums"
        
        return recommendations