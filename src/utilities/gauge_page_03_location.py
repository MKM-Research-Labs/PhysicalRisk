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

# src/utilities/gauge_page_03_location.py

"""
Page 3: Location and Geographic Context
Handles gauge location information, geographic positioning, and regional context.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeLocationPage(GaugeBasePage):
    """Generates the location page with geographic positioning and context."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate location page elements."""
        elements = []
        
        try:
            # Extract gauge ID for reference
            gauge_id = self._get_gauge_id(gauge_data)
            
            # LOCATION SECTION
            elements.append(Paragraph("Geographic Location and Context", self.styles['Title']))
            elements.append(Paragraph(f"Gauge ID: {gauge_id}", self.styles['SubTitle']))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # GEOGRAPHIC COORDINATES SECTION
            elements.append(Paragraph("Geographic Coordinates", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            sensor_details = flood_gauge_data.get('SensorDetails', {})
            gauge_info = sensor_details.get('GaugeInformation', {})
            
            # Create coordinates table
            coords_data = [["Geographic Parameter", "Value"]]
            
            # Coordinate fields
            coord_fields = [
                ('GaugeLatitude', 'Latitude'),
                ('GaugeLongitude', 'Longitude'),
                ('GroundLevelMeters', 'Ground Level Elevation')
            ]
            
            for field, label in coord_fields:
                value = gauge_info.get(field)
                if value is not None:
                    if 'Latitude' in label or 'Longitude' in label:
                        formatted_value = f"{self._format_coordinate(value)}°"
                    elif 'Elevation' in label:
                        formatted_value = self._format_measurement(value, 'm above sea level')
                    else:
                        formatted_value = self._format_value(value)
                    coords_data.append([label, formatted_value])
            
            coords_table = Table(coords_data, colWidths=self.table_widths['two_col'])
            coords_table.setStyle(self.table_styles['location'])
            elements.append(coords_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # THAMES RIVER CONTEXT SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Thames River Context", self.styles['SectionHeader']))
            
            thames_info = flood_gauge_data.get('ThamesInfo', {})
            thames_data = [["Thames Parameter", "Value"]]
            
            # Thames context fields
            thames_fields = [
                ('DistanceToThamesMeters', 'Distance to Thames')
            ]
            
            for field, label in thames_fields:
                value = thames_info.get(field)
                if value is not None:
                    if value == 0:
                        formatted_value = "On Thames River"
                    else:
                        formatted_value = self._format_measurement(value, 'm')
                    thames_data.append([label, formatted_value])
            
            thames_table = Table(thames_data, colWidths=self.table_widths['two_col'])
            thames_table.setStyle(self.table_styles['location'])
            elements.append(thames_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FLOOD RISK ASSESSMENT SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Location-Based Flood Risk Assessment", self.styles['SectionHeader']))
            
            flood_risk = thames_info.get('FloodRiskAssessment', {})
            risk_data = [["Risk Parameter", "Assessment"]]
            
            # Risk assessment fields
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
                    else:
                        formatted_value = self._format_value(value)
                    risk_data.append([label, formatted_value])
            
            risk_table = Table(risk_data, colWidths=self.table_widths['two_col'])
            risk_table.setStyle(self.table_styles['flood_risk'])
            elements.append(risk_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # GAUGE POSITIONING SUMMARY SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Gauge Positioning Summary", self.styles['SectionHeader']))
            
            # Create positioning summary
            summary_data = [["Position Attribute", "Description"]]
            
            # Calculate derived positioning information
            latitude = gauge_info.get('GaugeLatitude')
            longitude = gauge_info.get('GaugeLongitude')
            distance_to_thames = thames_info.get('DistanceToThamesMeters', 0)
            
            if latitude is not None:
                if latitude > 51.5:
                    lat_desc = "North London area"
                elif latitude > 51.4:
                    lat_desc = "Central London area"
                else:
                    lat_desc = "South London area"
                summary_data.append(["Regional Position", lat_desc])
            
            if distance_to_thames == 0:
                summary_data.append(["River Position", "Directly on Thames River"])
            elif distance_to_thames is not None and distance_to_thames < 100:
                summary_data.append(["River Position", f"Very close to Thames ({distance_to_thames}m)"])
            
            # Add risk category summary
            risk_category = flood_risk.get('FloodRiskCategory')
            if risk_category:
                summary_data.append(["Location Risk Profile", f"{risk_category} flood risk location"])
            
            summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
            summary_table.setStyle(self.table_styles['standard'])
            elements.append(summary_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating location information: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'