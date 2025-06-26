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

# src/utilities/page_05_risk_assessment.py

"""
Page 5: Risk Assessment
Handles comprehensive property risk analysis including flood, environmental, and location-based risks.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class RiskAssessmentPage(BasePage):
    """Generates property risk assessment page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate risk assessment page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Property Risk Assessment", self.styles['SectionHeader']))
            
            header_data = property_data.get('PropertyHeader', {})
            risk_data = header_data.get('RiskAssessment', {})
            
            # FLOOD RISK ASSESSMENT
            elements.append(Paragraph("Flood Risk Analysis", self.styles['SubSectionHeader']))
            
            flood_data = [["Risk Factor", "Assessment"]]
            
            # Environment Agency flood zone
            ea_zone = risk_data.get('EAFloodZone')
            if ea_zone:
                flood_data.append(["EA Flood Zone", ea_zone])
                
                # Interpret flood zone
                zone_interpretation = self._interpret_flood_zone(ea_zone)
                flood_data.append(["Zone Risk Level", zone_interpretation])
            
            # Overall flood risk
            overall_risk = risk_data.get('OverallFloodRisk')
            if overall_risk:
                flood_data.append(["Overall Flood Risk", overall_risk])
            
            # Flood risk type
            risk_type = risk_data.get('FloodRiskType')
            if risk_type:
                flood_data.append(["Risk Type", risk_type])
            
            # Last flood date
            last_flood = risk_data.get('LastFloodDate')
            if last_flood:
                flood_data.append(["Last Flood Date", last_flood])
            
            flood_table = Table(flood_data, colWidths=self.table_widths['two_col'])
            flood_table.setStyle(self.table_styles['risk'])
            elements.append(flood_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ELEVATION AND WATER PROXIMITY
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Elevation & Water Proximity", self.styles['SubSectionHeader']))
            
            elevation_data = [["Geographic Factor", "Measurement"]]
            
            # Ground elevation
            ground_level = risk_data.get('GroundLevelMeters')
            if isinstance(ground_level, (int, float)):
                elevation_data.append(["Ground Elevation", f"{ground_level:.2f} m above sea level"])
                
                # Elevation risk assessment
                if ground_level < 5:
                    elevation_risk = "High risk - Very low elevation"
                elif ground_level < 10:
                    elevation_risk = "Medium risk - Low elevation"
                elif ground_level < 20:
                    elevation_risk = "Low-medium risk - Moderate elevation"
                else:
                    elevation_risk = "Low risk - Good elevation"
                
                elevation_data.append(["Elevation Risk", elevation_risk])
            
            # Distance to water bodies
            river_distance = risk_data.get('RiverDistanceMeters')
            if isinstance(river_distance, (int, float)):
                elevation_data.append(["River Distance", f"{river_distance:.0f} m"])
                
                if river_distance < 100:
                    river_risk = "High risk - Very close to river"
                elif river_distance < 500:
                    river_risk = "Medium risk - Close to river"
                elif river_distance < 1000:
                    river_risk = "Low-medium risk - Moderate distance"
                else:
                    river_risk = "Low risk - Good distance from river"
                
                elevation_data.append(["River Proximity Risk", river_risk])
            
            # Coastal distance
            coastal_distance = risk_data.get('CoastalDistanceMeters')
            if isinstance(coastal_distance, (int, float)):
                coastal_km = coastal_distance / 1000
                elevation_data.append(["Coastal Distance", f"{coastal_km:.1f} km"])
            
            # Lake distance
            lake_distance = risk_data.get('LakeDistanceMeters')
            if isinstance(lake_distance, (int, float)):
                elevation_data.append(["Lake Distance", f"{lake_distance:.0f} m"])
            
            # Canal distance
            canal_distance = risk_data.get('CanalDistanceMeters')
            if isinstance(canal_distance, (int, float)):
                elevation_data.append(["Canal Distance", f"{canal_distance:.0f} m"])
            
            elevation_table = Table(elevation_data, colWidths=self.table_widths['two_col'])
            elevation_table.setStyle(self.table_styles['standard'])
            elements.append(elevation_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ENVIRONMENTAL FACTORS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Environmental Risk Factors", self.styles['SubSectionHeader']))
            
            environmental_data = [["Environmental Factor", "Status"]]
            
            # Soil type
            soil_type = risk_data.get('SoilType')
            if soil_type:
                environmental_data.append(["Soil Type", soil_type])
                
                # Soil risk assessment
                soil_risk = self._assess_soil_risk(soil_type)
                environmental_data.append(["Soil Risk Level", soil_risk])
            
            environmental_table = Table(environmental_data, colWidths=self.table_widths['two_col'])
            environmental_table.setStyle(self.table_styles['standard'])
            elements.append(environmental_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FLOOD DEFENCES
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Flood Defence Systems", self.styles['SubSectionHeader']))
            
            defence_data = [["Defence System", "Status"]]
            
            # Government defence scheme
            govt_defence = risk_data.get('GovernmentDefenceScheme')
            if govt_defence is not None:
                defence_data.append(["Government Defence Scheme", self._format_value(govt_defence)])
                
                if govt_defence:
                    defence_data.append(["Defence Benefit", "Reduced flood risk from scheme"])
                else:
                    defence_data.append(["Defence Status", "No formal defence scheme"])
            
            defence_table = Table(defence_data, colWidths=self.table_widths['two_col'])
            defence_table.setStyle(self.table_styles['protection'])
            elements.append(defence_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # OVERALL RISK SUMMARY
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Risk Summary", self.styles['SubSectionHeader']))
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risk_data)
            
            summary_data = [["Risk Category", "Assessment"]]
            summary_data.append(["Overall Risk Level", risk_score['level']])
            summary_data.append(["Risk Score", f"{risk_score['score']}/10"])
            summary_data.append(["Primary Risk Factors", risk_score['primary_factors']])
            summary_data.append(["Recommended Actions", risk_score['recommendations']])
            
            summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
            summary_table.setStyle(self.table_styles['risk'])
            elements.append(summary_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating risk assessment: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _interpret_flood_zone(self, zone: str) -> str:
        """Interpret EA flood zone codes."""
        zone_interpretations = {
            'Zone 1': 'Low risk - Less than 1 in 1000 annual probability',
            'Zone 2': 'Medium risk - 1 in 1000 to 1 in 100 annual probability',
            'Zone 3a': 'High risk - Greater than 1 in 100 annual probability',
            'Zone 3b': 'Functional floodplain - Used for flood storage'
        }
        return zone_interpretations.get(zone, f'Unknown zone: {zone}')
    
    def _assess_soil_risk(self, soil_type: str) -> str:
        """Assess risk based on soil type."""
        soil_type_lower = soil_type.lower()
        
        if 'peat' in soil_type_lower:
            return 'High risk - Peat soils can shrink and subside'
        elif 'clay' in soil_type_lower:
            return 'Medium-high risk - Clay can shrink and swell'
        elif 'sand' in soil_type_lower:
            return 'Medium risk - Sandy soils drain well but can be unstable'
        elif 'rock' in soil_type_lower or 'bedrock' in soil_type_lower:
            return 'Low risk - Stable foundation conditions'
        else:
            return f'Assessment required - {soil_type} characteristics need evaluation'
    
    def _calculate_risk_score(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall property risk score."""
        score = 0
        risk_factors = []
        
        # Flood risk scoring
        overall_flood = risk_data.get('OverallFloodRisk', '').lower()
        if 'very high' in overall_flood:
            score += 4
            risk_factors.append('Very High Flood Risk')
        elif 'high' in overall_flood:
            score += 3
            risk_factors.append('High Flood Risk')
        elif 'medium' in overall_flood:
            score += 2
            risk_factors.append('Medium Flood Risk')
        elif 'low' in overall_flood:
            score += 1
        
        # Elevation scoring
        ground_level = risk_data.get('GroundLevelMeters')
        if isinstance(ground_level, (int, float)):
            if ground_level < 5:
                score += 3
                risk_factors.append('Very Low Elevation')
            elif ground_level < 10:
                score += 2
                risk_factors.append('Low Elevation')
            elif ground_level < 20:
                score += 1
        
        # River proximity scoring
        river_distance = risk_data.get('RiverDistanceMeters')
        if isinstance(river_distance, (int, float)):
            if river_distance < 100:
                score += 2
                risk_factors.append('Very Close to River')
            elif river_distance < 500:
                score += 1
                risk_factors.append('Close to River')
        
        # Soil type scoring
        soil_type = risk_data.get('SoilType', '').lower()
        if 'peat' in soil_type:
            score += 2
            risk_factors.append('Peat Soil')
        elif 'clay' in soil_type:
            score += 1
            risk_factors.append('Clay Soil')
        
        # Determine risk level
        if score >= 8:
            level = 'Very High Risk'
            recommendations = 'Comprehensive flood protection and insurance essential'
        elif score >= 6:
            level = 'High Risk'
            recommendations = 'Flood protection measures strongly recommended'
        elif score >= 4:
            level = 'Medium Risk'
            recommendations = 'Consider flood protection measures'
        elif score >= 2:
            level = 'Low-Medium Risk'
            recommendations = 'Standard precautions adequate'
        else:
            level = 'Low Risk'
            recommendations = 'Minimal additional protection required'
        
        return {
            'score': score,
            'level': level,
            'primary_factors': ', '.join(risk_factors) if risk_factors else 'No major risk factors identified',
            'recommendations': recommendations
        }