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

# src/utilities/gauge_page_07_data_summary.py

"""
Page 7: Comprehensive Data Summary
Handles complete data overview, key metrics summary, and report conclusions.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeDataSummaryPage(GaugeBasePage):
    """Generates the comprehensive data summary page."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate data summary page elements."""
        elements = []
        
        try:
            # Extract gauge ID for reference
            gauge_id = self._get_gauge_id(gauge_data)
            gauge_name = self._get_gauge_name(gauge_data)
            
            # DATA SUMMARY SECTION
            elements.append(Paragraph("Comprehensive Data Summary", self.styles['Title']))
            elements.append(Paragraph(f"{gauge_name} ({gauge_id})", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # GAUGE OVERVIEW SUMMARY SECTION
            elements.append(Paragraph("Gauge Overview Summary", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            sensor_details = flood_gauge_data.get('SensorDetails', {})
            gauge_info = sensor_details.get('GaugeInformation', {})
            
            # Create gauge overview summary table
            overview_data = [["Summary Parameter", "Value"]]
            
            # Key summary fields
            summary_fields = [
                (gauge_info.get('GaugeType'), 'Gauge Type'),
                (gauge_info.get('ManufacturerName'), 'Manufacturer'),
                (gauge_info.get('OperationalStatus'), 'Operational Status'),
                (gauge_info.get('InstallationDate'), 'Installation Date'),
                (gauge_info.get('GaugeLatitude'), 'Latitude'),
                (gauge_info.get('GaugeLongitude'), 'Longitude')
            ]
            
            for value, label in summary_fields:
                if value is not None:
                    if 'Latitude' in label or 'Longitude' in label:
                        formatted_value = f"{self._format_coordinate(value)}°"
                    else:
                        formatted_value = self._format_value(value)
                    overview_data.append([label, formatted_value])
            
            overview_table = Table(overview_data, colWidths=self.table_widths['two_col'])
            overview_table.setStyle(self.table_styles['standard'])
            elements.append(overview_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # KEY METRICS SUMMARY SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Key Metrics Summary", self.styles['SectionHeader']))
            
            sensor_stats = flood_gauge_data.get('SensorStats', {})
            flood_stage = flood_gauge_data.get('FloodStage', {}).get('UK', {})
            thames_info = flood_gauge_data.get('ThamesInfo', {})
            
            metrics_data = [["Key Metric", "Value", "Significance"]]
            
            # Historical high level
            historical_high = sensor_stats.get('HistoricalHighLevel')
            if historical_high:
                severe_level = flood_stage.get('SevereFloodWarning')
                if severe_level and historical_high > severe_level:
                    significance = "Exceeds severe warning"
                else:
                    significance = "Within expected range"
                metrics_data.append([
                    "Historical High Level",
                    self._format_measurement(historical_high, 'm'),
                    significance
                ])
            
            # Flood alert levels
            flood_alert = flood_stage.get('FloodAlert')
            flood_warning = flood_stage.get('FloodWarning')
            severe_warning = flood_stage.get('SevereFloodWarning')
            
            if flood_alert:
                metrics_data.append([
                    "Flood Alert Level",
                    self._format_measurement(flood_alert, 'm'),
                    "Initial warning threshold"
                ])
            
            if severe_warning:
                metrics_data.append([
                    "Severe Warning Level",
                    self._format_measurement(severe_warning, 'm'),
                    "Critical action required"
                ])
            
            # Risk assessment
            flood_risk = thames_info.get('FloodRiskAssessment', {})
            risk_score = flood_risk.get('FloodRiskScore')
            risk_category = flood_risk.get('FloodRiskCategory')
            
            if risk_score and risk_category:
                metrics_data.append([
                    "Flood Risk Assessment",
                    f"{risk_score}/10 ({risk_category})",
                    "Overall location risk"
                ])
            
            # Exceedance frequency
            freq_exceed = sensor_stats.get('FrequencyExceedLevel3', 0)
            if freq_exceed == 0:
                freq_significance = "No severe exceedances"
            elif freq_exceed <= 2:
                freq_significance = "Low frequency events"
            else:
                freq_significance = "Regular severe events"
            
            metrics_data.append([
                "Severe Level Exceedances",
                self._format_frequency(freq_exceed),
                freq_significance
            ])
            
            metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2*inch, 3*inch])
            metrics_table.setStyle(self.table_styles['standard'])
            elements.append(metrics_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # OPERATIONAL STATUS SUMMARY SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Operational Status Summary", self.styles['SectionHeader']))
            
            measurements = sensor_details.get('Measurements', {})
            
            operational_data = [["Operational Parameter", "Status"]]
            
            # Operational summary fields
            op_fields = [
                (gauge_info.get('OperationalStatus'), 'Current Status'),
                (gauge_info.get('CertificationStatus'), 'Certification'),
                (measurements.get('MeasurementFrequency'), 'Measurement Frequency'),
                (measurements.get('DataTransmission'), 'Data Transmission'),
                (gauge_info.get('MaintenanceSchedule'), 'Maintenance Schedule')
            ]
            
            for value, label in op_fields:
                if value is not None:
                    operational_data.append([label, self._format_value(value)])
            
            operational_table = Table(operational_data, colWidths=self.table_widths['two_col'])
            operational_table.setStyle(self.table_styles['sensor'])
            elements.append(operational_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CURRENT STATUS SUMMARY SECTION (if timeseries data available)
            if timeseries_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Status Summary", self.styles['SectionHeader']))
                
                readings = timeseries_data.get('readings', [])
                if readings:
                    latest_reading = readings[-1]
                    
                    current_data = [["Current Parameter", "Value"]]
                    
                    # Current status fields
                    current_fields = [
                        (latest_reading.get('timestamp'), 'Last Reading'),
                        (latest_reading.get('waterLevel'), 'Current Water Level'),
                        (latest_reading.get('alertStatus'), 'Alert Status'),
                        (latest_reading.get('exceedsAlert'), 'Exceeds Alert'),
                        (latest_reading.get('exceedsWarning'), 'Exceeds Warning'),
                        (latest_reading.get('exceedsSevere'), 'Exceeds Severe')
                    ]
                    
                    for value, label in current_fields:
                        if value is not None:
                            if 'Level' in label and isinstance(value, (int, float)):
                                formatted_value = self._format_measurement(value, 'm')
                            else:
                                formatted_value = self._format_value(value)
                            current_data.append([label, formatted_value])
                    
                    current_table = Table(current_data, colWidths=self.table_widths['two_col'])
                    current_table.setStyle(self.table_styles['measurement'])
                    elements.append(current_table)
                    elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # REPORT CONCLUSIONS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Report Conclusions", self.styles['SectionHeader']))
            
            # Generate conclusions based on data
            conclusions = []
            
            # Gauge status conclusion
            status = gauge_info.get('OperationalStatus', '').lower()
            if 'operational' in status:
                conclusions.append("• Gauge is fully operational and providing reliable data")
            
            # Risk conclusion
            if risk_category:
                if risk_category.lower() == 'high':
                    conclusions.append("• Location presents high flood risk requiring close monitoring")
                elif risk_category.lower() == 'moderate':
                    conclusions.append("• Moderate flood risk location with standard monitoring protocols")
                else:
                    conclusions.append("• Low flood risk location with routine monitoring sufficient")
            
            # Historical pattern conclusion
            if freq_exceed == 0:
                conclusions.append("• No historical severe flood events recorded at this location")
            elif freq_exceed <= 2:
                conclusions.append("• Limited historical severe flood events indicate stable conditions")
            else:
                conclusions.append("• Multiple severe flood events indicate active flood-prone location")
            
            # Current status conclusion (if available)
            if timeseries_data and readings:
                alert_status = latest_reading.get('alertStatus', '').lower()
                if alert_status == 'severe':
                    conclusions.append("• CRITICAL: Current readings indicate severe flood conditions")
                elif alert_status == 'warning':
                    conclusions.append("• WARNING: Current readings indicate elevated flood risk")
                elif alert_status == 'alert':
                    conclusions.append("• ALERT: Current readings indicate increased flood monitoring required")
                else:
                    conclusions.append("• Current readings indicate normal water levels")
            
            # Maintenance conclusion
            cert_status = gauge_info.get('CertificationStatus', '').lower()
            if 'certified' in cert_status:
                conclusions.append("• Gauge meets certification standards for reliable flood monitoring")
            
            for conclusion in conclusions:
                elements.append(Paragraph(conclusion, self.styles['Normal']))
                elements.append(Spacer(1, self.spacing['paragraph']))
            
            # Report completion
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph(
                f"Report completed: {datetime.now().strftime('%Y-%m-%d %H:%M')} - MKM Research Labs", 
                self.styles['Normal']
            ))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating data summary: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'
    
    def _get_gauge_name(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge name from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeName']
        except (KeyError, TypeError):
            return 'Unknown Gauge Name'