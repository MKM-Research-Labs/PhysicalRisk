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

# src/utilities/gauge_page_05_flood_stages.py

"""
Page 5: Flood Stages and Alert Thresholds
Handles flood warning levels, alert thresholds, and stage classifications.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeFloodStagesPage(GaugeBasePage):
    """Generates the flood stages page with alert thresholds and classifications."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate flood stages page elements."""
        elements = []
        
        try:
            # Extract gauge ID for reference
            gauge_id = self._get_gauge_id(gauge_data)
            
            # FLOOD STAGES SECTION
            elements.append(Paragraph("Flood Stages and Alert Thresholds", self.styles['Title']))
            elements.append(Paragraph(f"Gauge ID: {gauge_id}", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # UK FLOOD STAGE THRESHOLDS SECTION
            elements.append(Paragraph("UK Flood Stage Thresholds", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            flood_stage = flood_gauge_data.get('FloodStage', {})
            uk_stages = flood_stage.get('UK', {})
            
            # Create flood thresholds table
            thresholds_data = [["Alert Level", "Threshold (m)", "Authority"]]
            
            # Decision body
            decision_body = uk_stages.get('DecisionBody', 'Not specified')
            
            # Threshold levels
            threshold_fields = [
                ('FloodAlert', 'Flood Alert'),
                ('FloodWarning', 'Flood Warning'),
                ('SevereFloodWarning', 'Severe Flood Warning')
            ]
            
            for field, label in threshold_fields:
                value = uk_stages.get(field)
                if value is not None:
                    thresholds_data.append([
                        label,
                        self._format_measurement(value, 'm'),
                        decision_body
                    ])
            
            thresholds_table = Table(thresholds_data, colWidths=self.table_widths['three_col'])
            thresholds_table.setStyle(self.table_styles['flood_risk'])
            elements.append(thresholds_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # THRESHOLD ANALYSIS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Threshold Analysis", self.styles['SectionHeader']))
            
            # Calculate threshold differences and analysis
            analysis_data = [["Analysis Parameter", "Value"]]
            
            flood_alert = uk_stages.get('FloodAlert')
            flood_warning = uk_stages.get('FloodWarning')
            severe_warning = uk_stages.get('SevereFloodWarning')
            
            if flood_alert and flood_warning:
                warning_diff = flood_warning - flood_alert
                analysis_data.append([
                    "Alert to Warning Range",
                    self._format_measurement(warning_diff, 'm')
                ])
            
            if flood_warning and severe_warning:
                severe_diff = severe_warning - flood_warning
                analysis_data.append([
                    "Warning to Severe Range", 
                    self._format_measurement(severe_diff, 'm')
                ])
            
            if flood_alert and severe_warning:
                total_range = severe_warning - flood_alert
                analysis_data.append([
                    "Total Alert Range",
                    self._format_measurement(total_range, 'm')
                ])
            
            # Add decision authority info
            analysis_data.append(["Decision Authority", decision_body])
            
            analysis_table = Table(analysis_data, colWidths=self.table_widths['two_col'])
            analysis_table.setStyle(self.table_styles['standard'])
            elements.append(analysis_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # HISTORICAL EXCEEDANCE SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Historical Threshold Exceedance", self.styles['SectionHeader']))
            
            sensor_stats = flood_gauge_data.get('SensorStats', {})
            exceedance_data = [["Exceedance Parameter", "Historical Data"]]
            
            # Historical threshold exceedance
            exceedance_fields = [
                ('HistoricalHighLevel', 'Historical High Level'),
                ('HistoricalHighDate', 'Date of Historical High'),
                ('LastDateLevelExceedLevel3', 'Last Severe Level Exceeded'),
                ('FrequencyExceedLevel3', 'Severe Level Exceedance Count')
            ]
            
            for field, label in exceedance_fields:
                value = sensor_stats.get(field)
                if value is not None:
                    if 'Level' in label and isinstance(value, (int, float)):
                        formatted_value = self._format_measurement(value, 'm')
                    elif 'Count' in label:
                        formatted_value = self._format_frequency(value)
                    else:
                        formatted_value = self._format_value(value)
                    exceedance_data.append([label, formatted_value])
            
            exceedance_table = Table(exceedance_data, colWidths=self.table_widths['two_col'])
            exceedance_table.setStyle(self.table_styles['historical'])
            elements.append(exceedance_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CURRENT STATUS vs THRESHOLDS SECTION (if timeseries data available)
            if timeseries_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Status vs Thresholds", self.styles['SectionHeader']))
                
                readings = timeseries_data.get('readings', [])
                if readings:
                    latest_reading = readings[-1]
                    current_level = latest_reading.get('waterLevel')
                    
                    status_data = [["Threshold Comparison", "Status"]]
                    
                    if current_level is not None:
                        status_data.append([
                            "Current Water Level",
                            self._format_measurement(current_level, 'm')
                        ])
                        
                        # Compare against thresholds
                        if flood_alert and current_level >= flood_alert:
                            if severe_warning and current_level >= severe_warning:
                                status_data.append(["Alert Status", "SEVERE FLOOD WARNING"])
                            elif flood_warning and current_level >= flood_warning:
                                status_data.append(["Alert Status", "FLOOD WARNING"])
                            else:
                                status_data.append(["Alert Status", "FLOOD ALERT"])
                        else:
                            status_data.append(["Alert Status", "Normal"])
                        
                        # Add exceedance flags
                        for flag, label in [
                            ('exceedsAlert', 'Exceeds Alert Level'),
                            ('exceedsWarning', 'Exceeds Warning Level'),
                            ('exceedsSevere', 'Exceeds Severe Level')
                        ]:
                            value = latest_reading.get(flag)
                            if value is not None:
                                status_data.append([label, self._format_value(value)])
                    
                    status_table = Table(status_data, colWidths=self.table_widths['two_col'])
                    status_table.setStyle(self.table_styles['flood_risk'])
                    elements.append(status_table)
            else:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Status vs Thresholds", self.styles['SectionHeader']))
                elements.append(Paragraph(
                    "No current timeseries data available for threshold comparison.", 
                    self.styles['Normal']
                ))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating flood stages information: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'