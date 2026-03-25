# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
Gauge layer module for flood gauge visualization.

This module provides functionality for adding flood gauge locations,
status indicators, and detailed information popups to the map.
"""

import logging
from typing import Any, Dict, List, Optional

import folium

from config.visual import GAUGE_FLOOD_HIGH, GAUGE_FLOOD_MEDIUM
from ..utils import ColorSchemes, DataFormatter

logger = logging.getLogger(__name__)


class GaugeLayer:
    """
    Layer class for adding flood gauge markers and information to the map.

    This class handles the creation of gauge markers with status-based styling,
    detailed popups with gauge information, and flood threshold indicators.
    """

    def __init__(self):
        """Initialize the gauge layer."""
        self.layer_name = "Flood Gauges"
        self.show_status_colors = True
        self.show_flood_thresholds = True

        # Gauge icon mapping based on operational status
        self.status_icons = {
            'Fully operational': folium.Icon(color='green', icon='tint', prefix='fa'),
            'Maintenance required': folium.Icon(color='orange', icon='tint', prefix='fa'),
            'Temporarily offline': folium.Icon(color='red', icon='tint', prefix='fa'),
            'Decommissioned': folium.Icon(color='gray', icon='tint', prefix='fa'),
            'Unknown': folium.Icon(color='blue', icon='tint', prefix='fa')
        }

    def add_to_map(self, folium_map: folium.Map, loaded_data) -> folium.FeatureGroup:
        """
        Add gauge layer to the map.

        Args:
            folium_map: The Folium map to add the layer to
            loaded_data: LoadedData container with all data

        Returns:
            FeatureGroup containing all gauge elements
        """
        logger.info(f"Adding {self.layer_name} to map...")

        # Create feature group for gauge elements
        gauge_group = folium.FeatureGroup(name=self.layer_name)

        if not loaded_data.gauge_data:
            logger.warning("No gauge data available")
            return gauge_group

        # Extract gauge information
        gauges = self._extract_gauges(loaded_data.gauge_data)

        if not gauges:
            logger.warning("No valid gauge data found")
            return gauge_group

        # Extract gauge hazard curves and num_storms for flood frequency RAG
        self._gauge_hazard = {}
        self._num_storms = 10000  # default
        if hasattr(loaded_data, 'hazard_data') and loaded_data.hazard_data:
            self._num_storms = loaded_data.hazard_data.get('metadata', {}).get('num_storms', 10000)
            hc = loaded_data.hazard_data.get('hazard_curves', {})
            for gid, gdata in hc.items():
                if isinstance(gdata, dict):
                    self._gauge_hazard[gid] = gdata

        # Add gauges to map
        for gauge_info in gauges:
            self._add_gauge_marker(gauge_group, gauge_info, loaded_data.gauge_flood_info)

        # Add to map
        gauge_group.add_to(folium_map)

        logger.info(f"Added {len(gauges)} flood gauges to map")
        return gauge_group

    def _extract_gauges(self, gauge_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract gauge information from raw gauge data.

        Args:
            gauge_data: Raw gauge data dictionary

        Returns:
            List of processed gauge information
        """
        gauges = []

        # Try different possible key formats for compatibility
        raw_gauges = gauge_data.get('items', gauge_data.get('floodGauges', gauge_data.get('flood_gauges', [])))

        for gauge in raw_gauges:
            try:
                # Extract gauge information
                gauge_info = gauge.get('FloodGauge', {})
                header = gauge_info.get('Header', {})
                sensor_details = gauge_info.get('SensorDetails', {})
                gauge_information = sensor_details.get('GaugeInformation', {})

                # Get coordinates
                lat = gauge_information.get('GaugeLatitude')
                lon = gauge_information.get('GaugeLongitude')

                if lat is None or lon is None:
                    continue

                # Extract key information
                gauge_id = header.get('GaugeID', 'Unknown')
                gauge_name = header.get('GaugeName', '')
                gauge_type = gauge_information.get('GaugeType', 'Unknown')
                operational_status = gauge_information.get('OperationalStatus', 'Unknown')
                gauge_owner = gauge_information.get('GaugeOwner', 'Unknown')
                data_source = gauge_information.get('DataSourceType', 'Unknown')
                installation_date = gauge_information.get('InstallationDate', 'Unknown')
                certification_status = gauge_information.get('CertificationStatus', 'Unknown')

                # Extract measurement information
                measurements = sensor_details.get('Measurements', {})
                measurement_frequency = measurements.get('MeasurementFrequency', 'Unknown')
                measurement_method = measurements.get('MeasurementMethod', 'Unknown')
                data_transmission = measurements.get('DataTransmission', 'Unknown')

                # Extract flood stage information
                flood_stage = gauge_info.get('FloodStage', {}).get('UK', {})
                flood_alert = flood_stage.get('FloodAlert', 'N/A')
                flood_warning = flood_stage.get('FloodWarning', 'N/A')
                severe_warning = flood_stage.get('SevereFloodWarning', 'N/A')

                # Extract sensor statistics
                sensor_stats = gauge_info.get('SensorStats', {})
                historical_high = sensor_stats.get('HistoricalHighLevel', 'N/A')
                historical_high_date = sensor_stats.get('HistoricalHighDate', 'N/A')
                last_level3_date = sensor_stats.get('LastDateLevelExceedLevel3', 'N/A')
                frequency_exceed_level3 = sensor_stats.get('FrequencyExceedLevel3', 'N/A')

                # Extract ground elevation
                ground_elevation = gauge_information.get('GroundLevelMeters', 'N/A')

                processed_gauge = {
                    'gauge_id': gauge_id,
                    'gauge_name': gauge_name,
                    'lat': float(lat),
                    'lon': float(lon),
                    'gauge_type': gauge_type,
                    'operational_status': operational_status,
                    'gauge_owner': gauge_owner,
                    'data_source': data_source,
                    'installation_date': installation_date,
                    'certification_status': certification_status,
                    'ground_elevation': ground_elevation,
                    'measurement_frequency': measurement_frequency,
                    'measurement_method': measurement_method,
                    'data_transmission': data_transmission,
                    'flood_alert': flood_alert,
                    'flood_warning': flood_warning,
                    'severe_warning': severe_warning,
                    'historical_high': historical_high,
                    'historical_high_date': historical_high_date,
                    'last_level3_date': last_level3_date,
                    'frequency_exceed_level3': frequency_exceed_level3
                }

                gauges.append(processed_gauge)

            except Exception as e:
                logger.warning(f"Error extracting gauge data: {e}")
                continue

        return gauges

    def _add_gauge_marker(self, feature_group: folium.FeatureGroup, gauge_info: Dict[str, Any],
                         gauge_flood_info: Optional[Dict[str, Any]]) -> None:
        """
        Add a single gauge marker to the feature group.

        Args:
            feature_group: Folium FeatureGroup to add the marker to
            gauge_info: Processed gauge information
            gauge_flood_info: Optional flood information for gauges
        """
        try:
            # Get flood info for this gauge if available
            flood_info = {}
            if gauge_flood_info:
                flood_info = gauge_flood_info.get(gauge_info['gauge_id'], {})

            # Determine location description
            location_desc = self._get_location_description(gauge_info['lat'], gauge_info['lon'])

            # Create popup content
            popup_content = self._create_gauge_popup(gauge_info, flood_info, location_desc)

            # Create tooltip
            tooltip = self._create_gauge_tooltip(gauge_info)

            # Select icon based on hazard rate (if available) or operational status
            icon = self._get_gauge_icon(gauge_info, flood_info)

            # Create marker
            marker = folium.Marker(
                location=[gauge_info['lat'], gauge_info['lon']],
                popup=folium.Popup(popup_content, max_width=350),
                tooltip=tooltip,
                icon=icon
            )

            marker.add_to(feature_group)

        except Exception as e:
            logger.warning(f"Error creating gauge marker for {gauge_info.get('gauge_id', 'Unknown')}: {e}")

    def _create_gauge_popup(self, gauge_info: Dict[str, Any], flood_info: Dict[str, Any],
                           location_desc: str) -> str:
        """
        Create detailed popup content for a gauge marker.

        Args:
            gauge_info: Processed gauge information
            flood_info: Flood risk information
            location_desc: Human-readable location description

        Returns:
            HTML string for popup content
        """
        gauge_name = gauge_info.get('gauge_name', '')
        popup_content = f"""
        <div style="font-family: Arial; width: 320px; max-height: 400px; overflow-y: auto;">
            <h4 style="margin-bottom: 5px; color: #1a5276;">{gauge_name if gauge_name else 'Flood Gauge'}</h4>
            <p style="color: #566573; font-size: 0.9em;">ID: {gauge_info['gauge_id']}</p>
            <p style="color: #2874A6; margin-top: 10px;"><b>Location:</b> {location_desc}</p>
            <p style="color: #2874A6; margin-top: 5px;"><b>Coordinates:</b> {gauge_info['lat']:.4f}N, {gauge_info['lon']:.4f}E</p>

            <div style="background-color: #EBF5FB; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #1a5276;">Equipment Details</h5>
                <p><b>Type:</b> {gauge_info['gauge_type']}</p>
                <p><b>Owner:</b> {gauge_info['gauge_owner']}</p>
                <p><b>Status:</b> <span style="color: {ColorSchemes.get_operational_status_color(gauge_info['operational_status'])};">{gauge_info['operational_status']}</span></p>
                <p><b>Installed:</b> {gauge_info['installation_date']}</p>
            </div>

            <div style="background-color: #F5EEF8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #6C3483;">Sensor & Data</h5>
                <p><b>Ground Elevation:</b> {DataFormatter.safe_format_float(gauge_info['ground_elevation'])} m AOD</p>
                <p><b>Data Source:</b> {gauge_info['data_source']}</p>
                <p><b>Measurement:</b> {gauge_info['measurement_frequency']}, {gauge_info['measurement_method']}</p>
                <p><b>Certification:</b> {gauge_info['certification_status']}</p>
            </div>

            <div style="background-color: #FADBD8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #943126;">Flood Thresholds</h5>
                <p><b>Alert Level:</b> {DataFormatter.safe_format_float(gauge_info['flood_alert'])} m</p>
                <p><b>Warning Level:</b> {DataFormatter.safe_format_float(gauge_info['flood_warning'])} m</p>
                <p><b>Severe Warning:</b> {DataFormatter.safe_format_float(gauge_info['severe_warning'])} m</p>
            </div>

            <div style="background-color: #E8F8F5; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #148F77;">Historical Context</h5>
                <p><b>Historical High:</b> {DataFormatter.safe_format_float(gauge_info['historical_high'])} m (on {gauge_info['historical_high_date']})</p>
                <p><b>Last Level 3 Exceedance:</b> {gauge_info['last_level3_date']}</p>
                <p><b>Level 3 Exceedance Frequency:</b> {gauge_info['frequency_exceed_level3']} times</p>
            </div>
        </div>"""
        return popup_content

    def _get_gauge_flood_count(self, gauge_id: str) -> int:
        """Get warning-level flood count for a gauge from hazard data."""
        hc = self._gauge_hazard.get(gauge_id, {})
        warning_rate = hc.get('annual_hazard_rate_warning', 0)
        num_storms = hc.get('num_storms_simulated', self._num_storms)
        return round(warning_rate * num_storms)

    @staticmethod
    def _get_gauge_flood_frequency_label(flood_count: int) -> str:
        """Get RAG label for gauge flood frequency (scaled up from property)."""
        if flood_count > GAUGE_FLOOD_HIGH:
            return "High"
        elif flood_count >= GAUGE_FLOOD_MEDIUM:
            return "Medium"
        else:
            return "Low"

    def _get_gauge_icon(self, gauge_info: Dict[str, Any], flood_info: Dict[str, Any]) -> folium.Icon:
        """Get icon colored by flood frequency RAG.  Synthetic gauges are grey."""
        gauge_id = gauge_info.get('gauge_id', '')

        # Synthetic gauges always grey — visually distinct from real gauges
        if gauge_id.startswith('SYNTH-'):
            return folium.Icon(color='gray', icon='tint', prefix='fa')

        flood_count = self._get_gauge_flood_count(gauge_id)

        if flood_count > GAUGE_FLOOD_HIGH:
            color = 'red'
        elif flood_count >= GAUGE_FLOOD_MEDIUM:
            color = 'orange'
        else:
            color = 'green'

        return folium.Icon(color=color, icon='tint', prefix='fa')

    def _create_gauge_tooltip(self, gauge_info: Dict[str, Any]) -> str:
        """
        Create tooltip content for a gauge marker.

        Args:
            gauge_info: Processed gauge information

        Returns:
            Tooltip text
        """
        gauge_id = gauge_info['gauge_id']
        gauge_name = gauge_info.get('gauge_name', '')
        flood_count = self._get_gauge_flood_count(gauge_id)
        freq_label = self._get_gauge_flood_frequency_label(flood_count)
        label = gauge_name if gauge_name else gauge_id
        return f"{label} | {gauge_id} | Floods: {flood_count} ({freq_label}) | Alert: {DataFormatter.safe_format_float(gauge_info['flood_alert'])}m"

    def _get_location_description(self, lat: float, lon: float) -> str:
        """
        Generate a location description based on coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Human-readable location description
        """
        if lon < -0.5:
            return "West London area"
        elif lon < 0:
            return "Central London (near Canary Wharf)"
        elif lon < 0.5:
            return "East London area"
        else:
            return "Southeast of London"

    def configure(self, show_status_colors: bool = True, show_flood_thresholds: bool = True):
        """
        Configure gauge layer display options.

        Args:
            show_status_colors: Whether to use status-based colors for markers
            show_flood_thresholds: Whether to show flood threshold information
        """
        self.show_status_colors = show_status_colors
        self.show_flood_thresholds = show_flood_thresholds

        logger.info(f"Gauge layer configured: status_colors={show_status_colors}, thresholds={show_flood_thresholds}")

    def get_gauge_statistics(self, gauges: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for the gauges.

        Args:
            gauges: List of processed gauge information

        Returns:
            Dictionary with gauge statistics
        """
        if not gauges:
            return {}

        # Count by status
        status_counts = {}
        for gauge in gauges:
            status = gauge['operational_status']
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by type
        type_counts = {}
        for gauge in gauges:
            gauge_type = gauge['gauge_type']
            type_counts[gauge_type] = type_counts.get(gauge_type, 0) + 1

        # Count by owner
        owner_counts = {}
        for gauge in gauges:
            owner = gauge['gauge_owner']
            owner_counts[owner] = owner_counts.get(owner, 0) + 1

        return {
            'total_gauges': len(gauges),
            'status_distribution': status_counts,
            'type_distribution': type_counts,
            'owner_distribution': owner_counts,
            'operational_percentage': (status_counts.get('Fully operational', 0) / len(gauges)) * 100
        }
