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

# src/utilities/gauge_page_02_sensor_details.py

"""
Page 2: Sensor Details and Hardware Specifications
Handles sensor hardware information, specifications, and technical details.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeSensorDetailsPage(GaugeBasePage):
    """Generates the sensor details page with hardware specifications."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate sensor details page elements."""
        elements = []
        
        try:
            # Extract gauge ID for reference
            gauge_id = self._get_gauge_id(gauge_data)
            
            # SENSOR DETAILS SECTION
            elements.append(Paragraph("Sensor Details and Hardware Specifications", self.styles['Title']))
            elements.append(Paragraph(f"Gauge ID: {gauge_id}", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # GAUGE INFORMATION SECTION
            elements.append(Paragraph("Gauge Information", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            sensor_details = flood_gauge_data.get('SensorDetails', {})
            gauge_info = sensor_details.get('GaugeInformation', {})
            
            # Create gauge information table
            gauge_info_data = [["Gauge Specification", "Value"]]
            
            # Key gauge information fields
            gauge_fields = [
                'DataSourceType', 'GaugeOwner', 'GaugeType', 'ManufacturerName',
                'InstallationDate', 'LastInspectionDate', 'MaintenanceSchedule',
                'OperationalStatus', 'CertificationStatus'
            ]
            
            for field in gauge_fields:
                value = gauge_info.get(field)
                if value is not None:
                    gauge_info_data.append([
                        self._format_field_name(field), 
                        self._format_value(value)
                    ])
            
            gauge_info_table = Table(gauge_info_data, colWidths=self.table_widths['two_col'])
            gauge_info_table.setStyle(self.table_styles['sensor'])
            elements.append(gauge_info_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # LOCATION INFORMATION SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Location Information", self.styles['SectionHeader']))
            
            location_data = [["Location Attribute", "Value"]]
            
            # Location fields
            location_fields = [
                ('GaugeLatitude', 'Latitude'),
                ('GaugeLongitude', 'Longitude'),
                ('GroundLevelMeters', 'Ground Level (m)')
            ]
            
            for field, label in location_fields:
                value = gauge_info.get(field)
                if value is not None:
                    if 'Latitude' in label or 'Longitude' in label:
                        formatted_value = self._format_coordinate(value)
                    elif 'Level' in label:
                        formatted_value = self._format_measurement(value, 'm')
                    else:
                        formatted_value = self._format_value(value)
                    location_data.append([label, formatted_value])
            
            location_table = Table(location_data, colWidths=self.table_widths['two_col'])
            location_table.setStyle(self.table_styles['location'])
            elements.append(location_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # MEASUREMENT CONFIGURATION SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Measurement Configuration", self.styles['SectionHeader']))
            
            measurements = sensor_details.get('Measurements', {})
            measurement_data = [["Measurement Parameter", "Configuration"]]
            
            # Measurement fields
            measurement_fields = [
                'MeasurementFrequency', 'MeasurementMethod', 'DataTransmission',
                'DataCurator', 'DataAccessMethod'
            ]
            
            for field in measurement_fields:
                value = measurements.get(field)
                if value is not None:
                    measurement_data.append([
                        self._format_field_name(field), 
                        self._format_value(value)
                    ])
            
            measurement_table = Table(measurement_data, colWidths=self.table_widths['two_col'])
            measurement_table.setStyle(self.table_styles['measurement'])
            elements.append(measurement_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # SENSOR STATISTICS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Historical Sensor Statistics", self.styles['SectionHeader']))
            
            sensor_stats = flood_gauge_data.get('SensorStats', {})
            stats_data = [["Statistical Measure", "Value"]]
            
            # Statistics fields
            stats_fields = [
                ('HistoricalHighLevel', 'Historical High Level (m)'),
                ('HistoricalHighDate', 'Date of Historical High'),
                ('LastDateLevelExceedLevel3', 'Last Severe Level Exceeded'),
                ('FrequencyExceedLevel3', 'Frequency of Severe Level Exceedance')
            ]
            
            for field, label in stats_fields:
                value = sensor_stats.get(field)
                if value is not None:
                    if 'Level (m)' in label:
                        formatted_value = self._format_measurement(value, 'm')
                    elif 'Frequency' in label:
                        formatted_value = self._format_frequency(value)
                    else:
                        formatted_value = self._format_value(value)
                    stats_data.append([label, formatted_value])
            
            stats_table = Table(stats_data, colWidths=self.table_widths['two_col'])
            stats_table.setStyle(self.table_styles['historical'])
            elements.append(stats_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating sensor details: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'