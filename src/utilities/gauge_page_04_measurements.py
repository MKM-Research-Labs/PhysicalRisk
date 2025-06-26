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

# src/utilities/gauge_page_04_measurements.py

"""
Page 4: Current Measurements and Operational Status
Handles current gauge readings, measurement status, and operational data.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeMeasurementsPage(GaugeBasePage):
    """Generates the measurements page with current readings and operational status."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate measurements page elements."""
        elements = []
        
        try:
            # Extract gauge ID for reference
            gauge_id = self._get_gauge_id(gauge_data)
            
            # MEASUREMENTS SECTION
            elements.append(Paragraph("Current Measurements and Operational Status", self.styles['Title']))
            elements.append(Paragraph(f"Gauge ID: {gauge_id}", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # MEASUREMENT CONFIGURATION SECTION
            elements.append(Paragraph("Measurement Configuration", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            sensor_details = flood_gauge_data.get('SensorDetails', {})
            measurements = sensor_details.get('Measurements', {})
            
            # Create measurement config table
            config_data = [["Measurement Parameter", "Configuration"]]
            
            # Measurement configuration fields
            config_fields = [
                'MeasurementFrequency', 'MeasurementMethod', 'DataTransmission',
                'DataCurator', 'DataAccessMethod'
            ]
            
            for field in config_fields:
                value = measurements.get(field)
                if value is not None:
                    config_data.append([
                        self._format_field_name(field), 
                        self._format_value(value)
                    ])
            
            config_table = Table(config_data, colWidths=self.table_widths['two_col'])
            config_table.setStyle(self.table_styles['measurement'])
            elements.append(config_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # GAUGE OPERATIONAL STATUS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Gauge Operational Status", self.styles['SectionHeader']))
            
            gauge_info = sensor_details.get('GaugeInformation', {})
            status_data = [["Status Parameter", "Current State"]]
            
            # Operational status fields
            status_fields = [
                ('OperationalStatus', 'Operational Status'),
                ('CertificationStatus', 'Certification Status'),
                ('LastInspectionDate', 'Last Inspection'),
                ('MaintenanceSchedule', 'Maintenance Schedule')
            ]
            
            for field, label in status_fields:
                value = gauge_info.get(field)
                if value is not None:
                    status_data.append([label, self._format_value(value)])
            
            status_table = Table(status_data, colWidths=self.table_widths['two_col'])
            status_table.setStyle(self.table_styles['sensor'])
            elements.append(status_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # HISTORICAL MEASUREMENT STATISTICS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Historical Measurement Statistics", self.styles['SectionHeader']))
            
            sensor_stats = flood_gauge_data.get('SensorStats', {})
            stats_data = [["Statistical Measure", "Value"]]
            
            # Historical statistics fields
            stats_fields = [
                ('HistoricalHighLevel', 'Historical High Level'),
                ('HistoricalHighDate', 'Date of Historical High'),
                ('LastDateLevelExceedLevel3', 'Last Severe Level Exceeded'),
                ('FrequencyExceedLevel3', 'Severe Level Exceedance Frequency')
            ]
            
            for field, label in stats_fields:
                value = sensor_stats.get(field)
                if value is not None:
                    if 'Level' in label and isinstance(value, (int, float)):
                        formatted_value = self._format_measurement(value, 'm')
                    elif 'Frequency' in label:
                        formatted_value = self._format_frequency(value)
                    else:
                        formatted_value = self._format_value(value)
                    stats_data.append([label, formatted_value])
            
            stats_table = Table(stats_data, colWidths=self.table_widths['two_col'])
            stats_table.setStyle(self.table_styles['historical'])
            elements.append(stats_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CURRENT READINGS SECTION (if timeseries data available)
            if timeseries_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Readings", self.styles['SectionHeader']))
                
                # Extract latest reading if available
                readings = timeseries_data.get('readings', [])
                if readings:
                    latest_reading = readings[-1]  # Get most recent
                    
                    current_data = [["Reading Parameter", "Current Value"]]
                    
                    # Current reading fields
                    reading_fields = [
                        ('timestamp', 'Last Reading Time'),
                        ('waterLevel', 'Current Water Level'),
                        ('alertStatus', 'Alert Status'),
                        ('exceedsAlert', 'Exceeds Alert Level'),
                        ('exceedsWarning', 'Exceeds Warning Level'),
                        ('exceedsSevere', 'Exceeds Severe Level')
                    ]
                    
                    for field, label in reading_fields:
                        value = latest_reading.get(field)
                        if value is not None:
                            if 'Level' in label and isinstance(value, (int, float)):
                                formatted_value = self._format_measurement(value, 'm')
                            else:
                                formatted_value = self._format_value(value)
                            current_data.append([label, formatted_value])
                    
                    current_table = Table(current_data, colWidths=self.table_widths['two_col'])
                    current_table.setStyle(self.table_styles['measurement'])
                    elements.append(current_table)
            else:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Current Readings", self.styles['SectionHeader']))
                elements.append(Paragraph(
                    "No current timeseries data available for real-time readings.", 
                    self.styles['Normal']
                ))
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating measurements information: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'