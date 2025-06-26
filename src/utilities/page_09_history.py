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

# src/utilities/page_09_history.py

"""
Page 9: Property History
Handles historical events, environmental issues, and ground conditions.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class HistoryPage(BasePage):
    """Generates property history page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate property history page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Property History", self.styles['SectionHeader']))
            
            history_data = property_data.get('History', {})
            
            if not history_data:
                elements.append(Paragraph("No historical data available.", self.styles['Normal']))
                return elements
            
            # ENVIRONMENTAL ISSUES
            environmental = history_data.get('EnvironmentalIssues', {})
            if environmental:
                elements.append(Paragraph("Environmental Conditions", self.styles['SubSectionHeader']))
                
                env_data = [["Environmental Factor", "Status"]]
                for key, value in environmental.items():
                    if value is not None:
                        env_data.append([self._format_field_name(key), self._format_value(value)])
                
                env_table = Table(env_data, colWidths=self.table_widths['two_col'])
                env_table.setStyle(self.table_styles['history'])
                elements.append(env_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FLOOD EVENTS
            flood_events = history_data.get('FloodEvents', {})
            if flood_events:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Flood History", self.styles['SubSectionHeader']))
                
                flood_data = [["Flood Information", "Details"]]
                
                # Flood return period
                return_period = flood_events.get('FloodReturnPeriod')
                if isinstance(return_period, (int, float)):
                    flood_data.append(["Flood Return Period", f"1 in {return_period} years"])
                
                # Other flood fields
                for key, value in flood_events.items():
                    if key != 'FloodReturnPeriod' and value is not None:
                        flood_data.append([self._format_field_name(key), self._format_value(value)])
                
                flood_table = Table(flood_data, colWidths=self.table_widths['two_col'])
                flood_table.setStyle(self.table_styles['history'])
                elements.append(flood_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FIRE INCIDENTS
            fire_incidents = history_data.get('FireIncidents', {})
            if fire_incidents:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Fire History", self.styles['SubSectionHeader']))
                
                fire_data = [["Fire Information", "Details"]]
                for key, value in fire_incidents.items():
                    if value is not None:
                        fire_data.append([self._format_field_name(key), self._format_value(value)])
                
                fire_table = Table(fire_data, colWidths=self.table_widths['two_col'])
                fire_table.setStyle(self.table_styles['history'])
                elements.append(fire_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # GROUND CONDITIONS
            ground_conditions = history_data.get('GroundConditions', {})
            if ground_conditions:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Ground Conditions", self.styles['SubSectionHeader']))
                
                ground_data = [["Ground Factor", "Status"]]
                for key, value in ground_conditions.items():
                    if value is not None:
                        ground_data.append([self._format_field_name(key), self._format_value(value)])
                
                ground_table = Table(ground_data, colWidths=self.table_widths['two_col'])
                ground_table.setStyle(self.table_styles['history'])
                elements.append(ground_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # HISTORICAL RISK ASSESSMENT
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Historical Risk Assessment", self.styles['SubSectionHeader']))
            
            risk_summary = self._assess_historical_risks(history_data)
            
            risk_data = [["Risk Category", "Assessment"]]
            for category, assessment in risk_summary.items():
                risk_data.append([category, assessment])
            
            risk_table = Table(risk_data, colWidths=self.table_widths['two_col'])
            risk_table.setStyle(self.table_styles['risk'])
            elements.append(risk_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating property history: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _assess_historical_risks(self, history_data: Dict[str, Any]) -> Dict[str, str]:
        """Assess risks based on historical data."""
        risk_summary = {}
        
        # Environmental risk assessment
        environmental = history_data.get('EnvironmentalIssues', {})
        if environmental:
            air_quality = environmental.get('AirQuality', '').lower()
            if 'poor' in air_quality or 'very high' in air_quality:
                risk_summary["Environmental Risk"] = "High - Poor air quality concerns"
            elif 'moderate' in air_quality:
                risk_summary["Environmental Risk"] = "Medium - Moderate environmental concerns"
            else:
                risk_summary["Environmental Risk"] = "Low - Good environmental conditions"
        
        # Flood risk from history
        flood_events = history_data.get('FloodEvents', {})
        if flood_events:
            damage_severity = flood_events.get('FloodDamageSeverity', '').lower()
            if 'severe' in damage_severity or 'major' in damage_severity:
                risk_summary["Historical Flood Risk"] = "High - Previous severe flood damage"
            elif 'moderate' in damage_severity:
                risk_summary["Historical Flood Risk"] = "Medium - Previous moderate damage"
            elif 'no damage' in damage_severity or 'none' in damage_severity:
                risk_summary["Historical Flood Risk"] = "Low - No previous flood damage"
        
        # Ground stability risk
        ground_conditions = history_data.get('GroundConditions', {})
        if ground_conditions:
            subsidence = ground_conditions.get('SubsidenceStatus', '').lower()
            if 'major' in subsidence or 'active' in subsidence:
                risk_summary["Ground Stability Risk"] = "High - Active ground movement"
            elif 'minor' in subsidence:
                risk_summary["Ground Stability Risk"] = "Medium - Minor ground movement"
            else:
                risk_summary["Ground Stability Risk"] = "Low - Stable ground conditions"
        
        return risk_summary