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

"""Gauge marker rendering: icons, popups, tooltips."""

import logging
from typing import Any, Dict, Optional

import folium

from config.visual import GAUGE_FLOOD_HIGH, GAUGE_FLOOD_MEDIUM
from ...utils import ColorSchemes, DataFormatter

logger = logging.getLogger(__name__)


def get_gauge_flood_count(gauge_id: str, gauge_hazard: dict,
                          num_storms: int) -> int:
    """Get warning-level flood count for a gauge from hazard data."""
    hc = gauge_hazard.get(gauge_id, {})
    warning_rate = hc.get('annual_hazard_rate_warning', 0)
    ns = hc.get('num_storms_simulated', num_storms)
    return round(warning_rate * ns)


def get_gauge_flood_frequency_label(flood_count: int) -> str:
    """Get RAG label for gauge flood frequency."""
    if flood_count > GAUGE_FLOOD_HIGH:
        return "High"
    elif flood_count >= GAUGE_FLOOD_MEDIUM:
        return "Medium"
    else:
        return "Low"


def get_gauge_icon(gauge_info: Dict[str, Any], gauge_hazard: dict,
                   num_storms: int) -> folium.Icon:
    """Get icon colored by operational status.

    Blue = Fully operational, Orange = Maintenance required,
    Red = Temporarily offline, Gray = Decommissioned.
    """
    status = gauge_info.get('operational_status', 'Unknown')
    status_color = {
        'Fully operational': 'blue',
        'Maintenance required': 'orange',
        'Temporarily offline': 'red',
        'Decommissioned': 'gray',
    }
    color = status_color.get(status, 'blue')

    return folium.Icon(color=color, icon='tint', prefix='fa')


def create_gauge_popup(gauge_info: Dict[str, Any], flood_info: Dict[str, Any],
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


def create_gauge_tooltip(gauge_info: Dict[str, Any], gauge_hazard: dict,
                         num_storms: int) -> str:
    """Create tooltip content for a gauge marker."""
    gauge_id = gauge_info['gauge_id']
    gauge_name = gauge_info.get('gauge_name', '')
    flood_count = get_gauge_flood_count(gauge_id, gauge_hazard, num_storms)
    freq_label = get_gauge_flood_frequency_label(flood_count)
    label = gauge_name if gauge_name else gauge_id
    return f"{label} | {gauge_id} | Floods: {flood_count} ({freq_label}) | Alert: {DataFormatter.safe_format_float(gauge_info['flood_alert'])}m"


def get_location_description(lat: float, lon: float) -> str:
    """Generate a location description based on coordinates.

    Describes the east/west position within the active catchment rather than a
    hardcoded London region, so it follows the catchment in play.
    """
    from config.visual import get_lon_position_label
    return get_lon_position_label(lon)


def add_gauge_marker(feature_group: folium.FeatureGroup,
                     gauge_info: Dict[str, Any],
                     gauge_flood_info: Optional[Dict[str, Any]],
                     gauge_hazard: dict,
                     num_storms: int) -> None:
    """
    Add a single gauge marker to the feature group.

    Args:
        feature_group: Folium FeatureGroup to add the marker to
        gauge_info: Processed gauge information
        gauge_flood_info: Optional flood information for gauges
        gauge_hazard: Hazard curve data keyed by gauge_id
        num_storms: Total storms simulated
    """
    try:
        # Get flood info for this gauge if available
        flood_info = {}
        if gauge_flood_info:
            flood_info = gauge_flood_info.get(gauge_info['gauge_id'], {})

        # Determine location description
        location_desc = get_location_description(gauge_info['lat'], gauge_info['lon'])

        # Create popup content
        popup_content = create_gauge_popup(gauge_info, flood_info, location_desc)

        # Create tooltip
        tooltip = create_gauge_tooltip(gauge_info, gauge_hazard, num_storms)

        # Select icon based on hazard rate
        icon = get_gauge_icon(gauge_info, gauge_hazard, num_storms)

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
