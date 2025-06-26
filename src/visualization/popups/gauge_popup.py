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

"""
Gauge popup creation functionality.

This module handles the creation of detailed popups for flood gauge markers,
including gauge information, operational status, flood thresholds, 
historical data, and flood risk data.
"""

from typing import Dict, Any, Optional
import folium
from .popup_builder import PopupBuilder


class GaugePopupBuilder(PopupBuilder):
    """Builder for gauge information popups."""
    
    def __init__(self):
        """Initialize the gauge popup builder."""
        super().__init__()
    
    def get_status_color(self, status: str) -> str:
        """
        Get color for operational status display.
        
        Args:
            status: Operational status string
            
        Returns:
            Color code for the status
        """
        colors = {
            'Fully operational': '#27AE60',
            'Maintenance required': '#F39C12',
            'Temporarily offline': '#C0392B',
            'Decommissioned': '#7F8C8D'
        }
        return colors.get(status, '#3498DB')
    
    def determine_location_description(self, lon: float) -> str:
        """
        Determine location description based on coordinates.
        
        Args:
            lon: Longitude coordinate
            
        Returns:
            Location description string
        """
        if lon < 0:
            return "Central London (near Canary Wharf)"
        elif lon > 0.3:
            return "Southeast of London"
        else:
            return "East London"
    
    def create_equipment_details_section(self, info: Dict[str, Any]) -> str:
        """
        Create the equipment details section for gauge popup.
        
        Args:
            info: Gauge information dictionary
            
        Returns:
            HTML string for equipment details section
        """
        gauge_info = info.get('SensorDetails', {}).get('GaugeInformation', {})
        
        gauge_owner = gauge_info.get('GaugeOwner', 'Unknown')
        gauge_type = gauge_info.get('GaugeType', 'Unknown')
        operational_status = gauge_info.get('OperationalStatus', 'Unknown')
        data_source = gauge_info.get('DataSourceType', 'Unknown')
        installation_date = gauge_info.get('InstallationDate', 'Unknown')
        certification_status = gauge_info.get('CertificationStatus', 'Unknown')
        
        status_color = self.get_status_color(operational_status)
        
        content = f"""
            {self.create_data_row("Type", gauge_type)}
            {self.create_data_row("Data Source", data_source)}
            {self.create_data_row("Owner", gauge_owner)}
            {self.create_data_row("Status", self.create_colored_text(operational_status, status_color))}
            {self.create_data_row("Certification", certification_status)}
            {self.create_data_row("Installed", installation_date)}
        """
        
        return self.create_section("Equipment Details", content)
    
    def create_measurement_approach_section(self, info: Dict[str, Any]) -> str:
        """
        Create the measurement approach section for gauge popup.
        
        Args:
            info: Gauge information dictionary
            
        Returns:
            HTML string for measurement approach section
        """
        measurements = info.get('SensorDetails', {}).get('Measurements', {})
        
        measurement_frequency = measurements.get('MeasurementFrequency', 'Unknown')
        measurement_method = measurements.get('MeasurementMethod', 'Unknown')
        data_transmission = measurements.get('DataTransmission', 'Unknown')
        
        content = f"""
            {self.create_data_row("Frequency", measurement_frequency)}
            {self.create_data_row("Method", measurement_method)}
            {self.create_data_row("Data Transmission", data_transmission)}
        """
        
        return self.create_section("Measurement Approach", content, "#FEF9E7", "#7D6608")
    
    def create_flood_thresholds_section(self, info: Dict[str, Any]) -> str:
        """
        Create the flood thresholds section for gauge popup.
        
        Args:
            info: Gauge information dictionary
            
        Returns:
            HTML string for flood thresholds section
        """
        flood_stage = info.get('FloodStage', {}).get('UK', {})
        
        flood_alert = flood_stage.get('FloodAlert', 'N/A')
        flood_warning = flood_stage.get('FloodWarning', 'N/A')
        severe_warning = flood_stage.get('SevereFloodWarning', 'N/A')
        
        content = f"""
            {self.create_data_row("Alert Level", f"{self.safe_format_float(flood_alert)} m")}
            {self.create_data_row("Warning Level", f"{self.safe_format_float(flood_warning)} m")}
            {self.create_data_row("Severe Warning", f"{self.safe_format_float(severe_warning)} m")}
        """
        
        return self.create_section("Flood Thresholds", content, "#FADBD8", "#943126")
    
    def create_historical_context_section(self, info: Dict[str, Any]) -> str:
        """
        Create the historical context section for gauge popup.
        
        Args:
            info: Gauge information dictionary
            
        Returns:
            HTML string for historical context section
        """
        sensor_stats = info.get('SensorStats', {})
        
        historical_high = sensor_stats.get('HistoricalHighLevel', 'N/A')
        historical_high_date = sensor_stats.get('HistoricalHighDate', 'N/A')
        last_level3_date = sensor_stats.get('LastDateLevelExceedLevel3', 'N/A')
        frequency_exceed_level3 = sensor_stats.get('FrequencyExceedLevel3', 'N/A')
        
        content = f"""
            {self.create_data_row("Historical High", f"{self.safe_format_float(historical_high)} m (on {historical_high_date})")}
            {self.create_data_row("Last Level 3 Exceedance", last_level3_date)}
            {self.create_data_row("Level 3 Exceedance Frequency", f"{frequency_exceed_level3} times")}
        """
        
        return self.create_section("Historical Context", content, "#E8F8F5", "#148F77")
    
    def create_flood_risk_data_section(self, flood_info: Dict[str, Any]) -> str:
        """
        Create the flood risk data section for gauge popup.
        
        Args:
            flood_info: Flood risk information dictionary
            
        Returns:
            HTML string for flood risk data section
        """
        if not flood_info:
            return ""
        
        max_level = flood_info.get("max_level", "N/A")
        alert_level = flood_info.get("alert_level", "N/A")
        warning_level = flood_info.get("warning_level", "N/A")
        severe_level = flood_info.get("severe_level", "N/A")
        max_gauge_reading = flood_info.get("max_gauge_reading", "N/A")
        
        content = f"""
            {self.create_data_row("Max Level", f"{self.safe_format_float(max_level)} m")}
            {self.create_data_row("Alert Level", f"{self.safe_format_float(alert_level)} m")}
            {self.create_data_row("Warning Level", f"{self.safe_format_float(warning_level)} m")}
            {self.create_data_row("Severe Level", f"{self.safe_format_float(severe_level)} m")}
            {self.create_data_row("Max Gauge Reading", f"{self.safe_format_float(max_gauge_reading)} m")}
        """
        
        return self.create_section("Flood Risk Data", content, "#FADBD8", "#943126")
    
    def create_complete_gauge_popup_content(self, gauge_id: str, lat: float, lon: float, 
                                          info: Dict[str, Any], 
                                          flood_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create complete popup content for a gauge marker.
        
        Args:
            gauge_id: Gauge identifier
            lat: Latitude coordinate
            lon: Longitude coordinate
            info: Gauge information dictionary
            flood_info: Optional flood risk information
            
        Returns:
            Complete HTML string for the gauge popup
        """
        # Determine location description
        location_desc = self.determine_location_description(lon)
        
        # Create header
        header = self.create_header("Flood Gauge Analysis", f"ID: {gauge_id}")
        
        # Location information - create as a paragraph, not a section
        location_content = f'<p style="color: #2874A6; margin-top: 10px;"><b>Location:</b> {location_desc} ({lat:.4f}°N, {lon:.4f}°E)</p>'
        
        # Create all sections
        equipment_section = self.create_equipment_details_section(info)
        measurement_section = self.create_measurement_approach_section(info)
        thresholds_section = self.create_flood_thresholds_section(info)
        historical_section = self.create_historical_context_section(info)
        flood_risk_section = self.create_flood_risk_data_section(flood_info) if flood_info else ""
        
        # Combine all content
        content = (header + location_content + equipment_section + measurement_section + 
                  thresholds_section + historical_section + flood_risk_section)
        
        return self.create_popup_wrapper(content)
    
    def build_gauge_popup(self, gauge_id: str, lat: float, lon: float, 
                         info: Dict[str, Any], 
                         flood_info: Optional[Dict[str, Any]] = None) -> folium.Popup:
        """
        Build a complete gauge popup.
        
        Args:
            gauge_id: Gauge identifier
            lat: Latitude coordinate
            lon: Longitude coordinate
            info: Gauge information dictionary
            flood_info: Optional flood risk information
            
        Returns:
            Folium Popup object ready to be attached to a marker
        """
        content = self.create_complete_gauge_popup_content(gauge_id, lat, lon, info, flood_info)
        return self.build_popup(content)
    
    def create_gauge_tooltip(self, gauge_type: str, operational_status: str, 
                           flood_alert: float) -> str:
        """
        Create tooltip text for gauge marker.
        
        Args:
            gauge_type: Type of gauge
            operational_status: Operational status
            flood_alert: Flood alert level
            
        Returns:
            Tooltip text string
        """
        return f"Gauge: {gauge_type} | Status: {operational_status} | Alert: {self.safe_format_float(flood_alert)}m"