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

# src/utilities/gauge_page_06_risk_assessment.py

"""
Page 6: Risk Assessment and Analysis
Handles flood risk analysis, historical patterns, and risk evaluation.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeRiskAssessmentPage(GaugeBasePage):
    """Generates the risk assessment page with flood risk analysis."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate risk assessment page elements."""
        elements = []
        
        try:
            # Extract gauge ID for reference
            gauge_id = self._get_gauge_id(gauge_data)
            
            # RISK ASSESSMENT SECTION
            elements.append(Paragraph("Flood Risk Assessment and Analysis", self.styles['Title']))
            elements.append(Paragraph(f"Gauge ID: {gauge_id}", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # OVERALL RISK PROFILE SECTION
            elements.append(Paragraph("Overall Risk Profile", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            thames_info = flood_gauge_data.get('ThamesInfo', {})
            flood_risk = thames_info.get('FloodRiskAssessment', {})
            
            # Create overall risk profile table
            profile_data = [["Risk Parameter", "Assessment"]]
            
            # Overall risk assessment fields
            risk_fields = [
                ('FloodRiskScore', 'Flood Risk Score'),
                ('FloodRiskCategory', 'Risk Category'),
                ('LastAssessmentDate', 'Last Assessment Date')
            ]
            
            for field, label in risk_fields:
                value = flood_risk.get(field)
                if value is not None:
                    if 'Score' in label and isinstance(value, (int, float)):
                        formatted_value = f"{value}/10"
                        if value >= 8:
                            formatted_value += " (Very High Risk)"
                        elif value >= 6:
                            formatted_value += " (High Risk)"
                        elif value >= 4:
                            formatted_value += " (Moderate Risk)"
                        else:
                            formatted_value += " (Low Risk)"
                    else:
                        formatted_value = self._format_value(value)
                    profile_data.append([label, formatted_value])
            
            # Add distance to Thames as risk factor
            distance_to_thames = thames_info.get('DistanceToThamesMeters', 0)
            if distance_to_thames == 0:
                profile_data.append(["Location Risk Factor", "On Thames River (Highest Risk)"])
            elif distance_to_thames < 100:
                profile_data.append(["Location Risk Factor", f"Very close to Thames ({distance_to_thames}m)"])
            
            profile_table = Table(profile_data, colWidths=self.table_widths['two_col'])
            profile_table.setStyle(self.table_styles['flood_risk'])
            elements.append(profile_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # HISTORICAL RISK PATTERNS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Historical Risk Patterns", self.styles['SectionHeader']))
            
            sensor_stats = flood_gauge_data.get('SensorStats', {})
            patterns_data = [["Historical Pattern", "Analysis"]]
            
            # Historical pattern analysis
            freq_exceed = sensor_stats.get('FrequencyExceedLevel3', 0)
            historical_high = sensor_stats.get('HistoricalHighLevel')
            last_exceed_date = sensor_stats.get('LastDateLevelExceedLevel3')
            
            # Frequency analysis
            if freq_exceed == 0:
                freq_analysis = "No severe level exceedances recorded"
            elif freq_exceed == 1:
                freq_analysis = "One severe level exceedance (Low frequency)"
            elif freq_exceed <= 3:
                freq_analysis = f"{freq_exceed} severe level exceedances (Moderate frequency)"
            else:
                freq_analysis = f"{freq_exceed} severe level exceedances (High frequency)"
            
            patterns_data.append(["Severe Level Frequency", freq_analysis])
            
            # Historical high analysis
            if historical_high:
                flood_stage = flood_gauge_data.get('FloodStage', {}).get('UK', {})
                severe_level = flood_stage.get('SevereFloodWarning')
                if severe_level and historical_high > severe_level:
                    high_analysis = f"{historical_high:.3f}m (Exceeded severe warning level)"
                else:
                    high_analysis = f"{historical_high:.3f}m"
                patterns_data.append(["Historical High Level", high_analysis])
            
            # Recent activity analysis
            if last_exceed_date:
                try:
                    last_year = int(last_exceed_date.split('-')[0])
                    current_year = datetime.now().year
                    years_since = current_year - last_year
                    if years_since <= 1:
                        recency_analysis = "Recent severe level activity (within 1 year)"
                    elif years_since <= 3:
                        recency_analysis = f"Moderate recent activity ({years_since} years ago)"
                    else:
                        recency_analysis = f"No recent severe activity ({years_since} years ago)"
                    patterns_data.append(["Recent Activity", recency_analysis])
                except (ValueError, AttributeError):
                    pass
            
            patterns_table = Table(patterns_data, colWidths=self.table_widths['two_col'])
            patterns_table.setStyle(self.table_styles['historical'])
            elements.append(patterns_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # THRESHOLD RISK ANALYSIS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Threshold Risk Analysis", self.styles['SectionHeader']))
            
            flood_stage = flood_gauge_data.get('FloodStage', {}).get('UK', {})
            threshold_data = [["Threshold Analysis", "Risk Assessment"]]
            
            # Threshold spacing analysis
            flood_alert = flood_stage.get('FloodAlert')
            flood_warning = flood_stage.get('FloodWarning')
            severe_warning = flood_stage.get('SevereFloodWarning')
            
            if flood_alert and flood_warning and severe_warning:
                warning_range = flood_warning - flood_alert
                severe_range = severe_warning - flood_warning
                
                if warning_range < 1.0:
                    range_analysis = f"Narrow alert range ({warning_range:.3f}m) - Rapid escalation risk"
                elif warning_range < 2.0:
                    range_analysis = f"Moderate alert range ({warning_range:.3f}m) - Standard escalation"
                else:
                    range_analysis = f"Wide alert range ({warning_range:.3f}m) - Gradual escalation"
                
                threshold_data.append(["Alert Range Analysis", range_analysis])
                
                # Historical vs threshold comparison
                if historical_high and severe_warning:
                    margin = historical_high - severe_warning
                    if margin > 1.0:
                        margin_analysis = f"Historical high exceeds severe level by {margin:.3f}m (High risk)"
                    elif margin > 0:
                        margin_analysis = f"Historical high exceeds severe level by {margin:.3f}m (Elevated risk)"
                    else:
                        margin_analysis = "Historical high within severe warning levels"
                    threshold_data.append(["Historical vs Threshold", margin_analysis])
            
            threshold_table = Table(threshold_data, colWidths=self.table_widths['two_col'])
            threshold_table.setStyle(self.table_styles['standard'])
            elements.append(threshold_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CURRENT RISK STATUS SECTION (if timeseries data available)
            if timeseries_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Risk Status", self.styles['SectionHeader']))
                
                readings = timeseries_data.get('readings', [])
                if readings:
                    latest_reading = readings[-1]
                    current_level = latest_reading.get('waterLevel')
                    alert_status = latest_reading.get('alertStatus', 'Unknown')
                    
                    current_data = [["Current Risk Parameter", "Status"]]
                    
                    if current_level:
                        current_data.append([
                            "Current Water Level",
                            self._format_measurement(current_level, 'm')
                        ])
                    
                    current_data.append(["Current Alert Status", alert_status])
                    
                    # Risk level assessment
                    if alert_status == "Severe":
                        risk_level = "CRITICAL RISK - Immediate attention required"
                    elif alert_status == "Warning":
                        risk_level = "HIGH RISK - Close monitoring required"
                    elif alert_status == "Alert":
                        risk_level = "ELEVATED RISK - Increased vigilance"
                    else:
                        risk_level = "NORMAL - Standard monitoring"
                    
                    current_data.append(["Risk Level Assessment", risk_level])
                    
                    current_table = Table(current_data, colWidths=self.table_widths['two_col'])
                    current_table.setStyle(self.table_styles['flood_risk'])
                    elements.append(current_table)
            else:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Risk Status", self.styles['SectionHeader']))
                elements.append(Paragraph(
                    "No current timeseries data available for real-time risk assessment.", 
                    self.styles['Normal']
                ))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating risk assessment: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'