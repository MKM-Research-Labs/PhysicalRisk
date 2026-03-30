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

"""
Flood gauge data loader for MKM Research Labs PRS Platform.

Handles loading and querying flood gauge portfolio data.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class GaugeLoader(BaseLoader[Dict[str, Any]]):
    """
    Loader for flood gauge portfolio data.

    Handles the gauge.json file with structure:
    {
        "floodGauges": [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": "...", "GaugeName": "..."},
                    "SensorDetails": {
                        "GaugeInformation": {...}
                    }
                }
            }
        ]
    }
    """

    ENTITY_NAME = 'gauge'
    DEFAULT_FILENAME = 'gauge.json'
    CONTAINER_KEYS = ['floodGauges', 'flood_gauges', 'gauges']

    def get_entity_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extract GaugeID from nested structure."""
        return (
            entity
            .get('FloodGauge', {})
            .get('Header', {})
            .get('GaugeID')
        )

    def get_entity_summary(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create gauge summary for listing."""
        flood_gauge = entity.get('FloodGauge', {})
        header = flood_gauge.get('Header', {})
        sensor_details = flood_gauge.get('SensorDetails', {})
        gauge_info = sensor_details.get('GaugeInformation', {})

        return {
            'gaugeId': header.get('GaugeID'),
            'name': header.get('GaugeName'),
            'type': gauge_info.get('GaugeType'),
            'owner': gauge_info.get('GaugeOwner'),
            'status': gauge_info.get('OperationalStatus'),
            'location': {
                'latitude': header.get('Latitude'),
                'longitude': header.get('Longitude'),
            }
        }

    # =========================================================================
    # Gauge-specific query methods
    # =========================================================================

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find gauge by name (partial match).

        Args:
            name: Gauge name to search for

        Returns:
            First matching gauge or None
        """
        name_lower = name.lower()
        for entity in self.load_all():
            gauge_name = (
                entity
                .get('FloodGauge', {})
                .get('Header', {})
                .get('GaugeName', '')
            )
            if name_lower in gauge_name.lower():
                return entity
        return None

    def find_by_owner(self, owner: str) -> List[Dict[str, Any]]:
        """
        Find all gauges owned by a specific organization.

        Args:
            owner: Owner name to filter by (e.g., 'USGS', 'Environment Agency')

        Returns:
            List of matching gauges
        """
        owner_lower = owner.lower()
        results = []
        for entity in self.load_all():
            gauge_owner = (
                entity
                .get('FloodGauge', {})
                .get('SensorDetails', {})
                .get('GaugeInformation', {})
                .get('GaugeOwner', '')
            )
            if owner_lower in gauge_owner.lower():
                results.append(entity)
        return results

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Find all gauges with a specific operational status.

        Args:
            status: Status to filter by (e.g., 'Active', 'Inactive', 'Maintenance')

        Returns:
            List of matching gauges
        """
        status_lower = status.lower()
        results = []
        for entity in self.load_all():
            gauge_status = (
                entity
                .get('FloodGauge', {})
                .get('SensorDetails', {})
                .get('GaugeInformation', {})
                .get('OperationalStatus', '')
            )
            if gauge_status.lower() == status_lower:
                results.append(entity)
        return results

    def find_by_type(self, gauge_type: str) -> List[Dict[str, Any]]:
        """
        Find all gauges of a specific type.

        Args:
            gauge_type: Type to filter by (e.g., 'River', 'Tidal', 'Coastal')

        Returns:
            List of matching gauges
        """
        type_lower = gauge_type.lower()
        results = []
        for entity in self.load_all():
            entity_type = (
                entity
                .get('FloodGauge', {})
                .get('SensorDetails', {})
                .get('GaugeInformation', {})
                .get('GaugeType', '')
            )
            if entity_type.lower() == type_lower:
                results.append(entity)
        return results

    def get_active_gauges(self) -> List[Dict[str, Any]]:
        """
        Get all active gauges.

        Returns:
            List of gauges with Active status
        """
        return self.find_by_status('Active')

    def get_coordinates(self, gauge_id: str) -> Optional[tuple]:
        """
        Get latitude/longitude for a gauge.

        Args:
            gauge_id: Gauge ID to look up

        Returns:
            Tuple of (latitude, longitude) or None
        """
        entity = self.find_by_id(gauge_id)
        if entity:
            header = entity.get('FloodGauge', {}).get('Header', {})
            lat = header.get('Latitude')
            lon = header.get('Longitude')
            if lat is not None and lon is not None:
                return (lat, lon)
        return None

    def get_flood_stages(self, gauge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get flood stage thresholds for a gauge.

        Args:
            gauge_id: Gauge ID to look up

        Returns:
            Flood stages dictionary or None
        """
        entity = self.find_by_id(gauge_id)
        if entity:
            return (
                entity
                .get('FloodGauge', {})
                .get('FloodStages')
            )
        return None

    def get_gauge_name(self, gauge_id: str) -> Optional[str]:
        """
        Get the human-readable name for a gauge.

        Args:
            gauge_id: Gauge ID to look up

        Returns:
            Gauge name or None
        """
        entity = self.find_by_id(gauge_id)
        if entity:
            return (
                entity
                .get('FloodGauge', {})
                .get('Header', {})
                .get('GaugeName')
            )
        return None

    def get_gauges_in_radius(
        self,
        lat: float,
        lon: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """
        Find all gauges within a radius of a point.

        Uses Haversine formula for distance calculation.

        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers

        Returns:
            List of gauges within radius
        """
        from .geo_utils import find_entities_in_radius

        def get_coords(entity):
            return self.get_coordinates(self.get_entity_id(entity))

        return find_entities_in_radius(
            self.load_all(), get_coords, lat, lon, radius_km
        )
