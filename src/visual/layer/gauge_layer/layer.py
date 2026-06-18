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

"""GaugeLayer — top-level orchestrator for gauge map layer."""

import logging
from typing import Any, Dict, List

import folium

from .extract import extract_gauges
from .marker import (
    add_gauge_marker,
    create_gauge_popup,
    create_gauge_tooltip,
    get_gauge_flood_count,
    get_gauge_flood_frequency_label,
    get_gauge_icon,
    get_location_description,
)

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
        gauges = extract_gauges(loaded_data.gauge_data)

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

        # Add gauges to map (skip synthetic — background-only for PRS)
        for gauge_info in gauges:
            if gauge_info.get('gauge_id', '').startswith('SYNTH-'):
                continue
            add_gauge_marker(
                gauge_group, gauge_info, loaded_data.gauge_flood_info,
                self._gauge_hazard, self._num_storms,
            )

        # Add to map
        gauge_group.add_to(folium_map)

        logger.info(f"Added {len(gauges)} flood gauges to map")
        return gauge_group

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

    # ------------------------------------------------------------------
    # Delegating methods — preserve backward-compatible instance API
    # ------------------------------------------------------------------

    def _extract_gauges(self, gauge_data):
        return extract_gauges(gauge_data)

    def _create_gauge_popup(self, gauge_info, flood_info, location_desc):
        return create_gauge_popup(gauge_info, flood_info, location_desc)

    def _create_gauge_tooltip(self, gauge_info):
        return create_gauge_tooltip(gauge_info, self._gauge_hazard, self._num_storms)

    def _get_location_description(self, lat, lon):
        return get_location_description(lat, lon)

    def _get_gauge_flood_count(self, gauge_id):
        return get_gauge_flood_count(gauge_id, self._gauge_hazard, self._num_storms)

    @staticmethod
    def _get_gauge_flood_frequency_label(flood_count):
        return get_gauge_flood_frequency_label(flood_count)

    def _add_gauge_marker(self, feature_group, gauge_info, gauge_flood_info):
        return add_gauge_marker(
            feature_group, gauge_info, gauge_flood_info,
            self._gauge_hazard, self._num_storms,
        )

    def _get_gauge_icon(self, gauge_info, flood_info):
        return get_gauge_icon(gauge_info, self._gauge_hazard, self._num_storms)
