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

# src/utilities/gauge_page_01_title_overview.py

"""
Page 1: Title and Gauge Overview
Handles the title page with basic gauge information and overview.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from reportlab.lib.units import inch
from .gauge_base_page import GaugeBasePage


class GaugeTitleOverviewPage(GaugeBasePage):
    """Generates the title page with gauge overview."""
    
    def generate_elements(self, gauge_data: Dict[str, Any], 
                         timeseries_data: Dict[str, Any] = None) -> List:
        """Generate title page elements."""
        elements = []
        
        try:
            # Extract gauge ID
            gauge_id = self._get_gauge_id(gauge_data)
            
            # TITLE SECTION
            elements.append(Paragraph(
                "Comprehensive Flood Gauge Analysis Report", 
                self.styles['Title']
            ))
            elements.append(Paragraph(
                f"Gauge ID: {gauge_id}", 
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", 
                self.styles['Normal']
            ))
            elements.append(Spacer(1, self.spacing['major_section']))
            
            # GAUGE OVERVIEW SECTION
            elements.append(Paragraph("Gauge Overview", self.styles['SectionHeader']))
            
            flood_gauge_data = gauge_data.get('FloodGauge', {})
            header_data = flood_gauge_data.get('Header', {})
            
            # Create overview table
            overview_data = [["Gauge Information", "Value"]]
            
            # Key overview fields
            key_fields = [
                'GaugeID', 'GaugeName'
            ]
            
            for field in key_fields:
                value = header_data.get(field)
                if value is not None:
                    overview_data.append([
                        self._format_field_name(field), 
                        self._format_value(value)
                    ])
            
            overview_table = Table(overview_data, colWidths=self.table_widths['two_col'])
            overview_table.setStyle(self.table_styles['standard'])
            elements.append(overview_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # GAUGE SUMMARY SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Gauge Summary", self.styles['SectionHeader']))
            
            # Create summary from key attributes
            sensor_details = flood_gauge_data.get('SensorDetails', {})
            gauge_info = sensor_details.get('GaugeInformation', {})
            sensor_stats = flood_gauge_data.get('SensorStats', {})
            flood_stage = flood_gauge_data.get('FloodStage', {}).get('UK', {})
            
            summary_data = [["Key Attribute", "Value"]]
            
            # Key summary fields
            summary_fields = [
                (gauge_info.get('GaugeType'), 'Gauge Type'),
                (gauge_info.get('GaugeOwner'), 'Gauge Owner'),
                (gauge_info.get('ManufacturerName'), 'Manufacturer'),
                (gauge_info.get('OperationalStatus'), 'Status'),
                (gauge_info.get('CertificationStatus'), 'Certification'),
                (sensor_stats.get('HistoricalHighLevel'), 'Historical High (m)'),
                (flood_stage.get('FloodAlert'), 'Flood Alert Level (m)'),
                (flood_stage.get('FloodWarning'), 'Flood Warning Level (m)')
            ]
            
            for value, label in summary_fields:
                if value is not None:
                    if 'Level' in label and isinstance(value, (int, float)):
                        formatted_value = self._format_measurement(value, 'm')
                    else:
                        formatted_value = self._format_value(value)
                    summary_data.append([label, formatted_value])
            
            # Add installation age if available
            install_date = gauge_info.get('InstallationDate')
            if install_date:
                try:
                    install_year = int(install_date.split('-')[0])
                    gauge_age = datetime.now().year - install_year
                    summary_data.append(["Gauge Age", f"{gauge_age} years"])
                except (ValueError, AttributeError):
                    pass
            
            summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
            summary_table.setStyle(self.table_styles['standard'])
            elements.append(summary_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating gauge title and overview: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _get_gauge_id(self, gauge_data: Dict[str, Any]) -> str:
        """Extract gauge ID from data."""
        try:
            return gauge_data['FloodGauge']['Header']['GaugeID']
        except (KeyError, TypeError):
            return 'Unknown Gauge'