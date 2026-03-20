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
Property data loader for MKM Research Labs PRS Platform.

Handles loading and querying property portfolio data.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class PropertyLoader(BaseLoader[Dict[str, Any]]):
    """
    Loader for property portfolio data.

    Handles the property.json file with structure:
    {
        "properties": [
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": "..."},
                    "Location": {"Address": "...", "City": "...", ...}
                },
                ...
            }
        ]
    }
    """

    ENTITY_NAME = 'property'
    DEFAULT_FILENAME = 'property.json'
    CONTAINER_KEYS = ['properties', 'portfolio']

    def get_entity_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extract PropertyID from nested structure."""
        return (
            entity
            .get('PropertyHeader', {})
            .get('Header', {})
            .get('PropertyID')
        )

    def get_entity_summary(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create property summary for listing."""
        header = entity.get('PropertyHeader', {})
        location = header.get('Location', {})
        details = header.get('Header', {})

        return {
            'propertyId': details.get('PropertyID'),
            'address': location.get('Address'),
            'city': location.get('City'),
            'state': location.get('State'),
            'zipCode': location.get('ZipCode'),
            'county': location.get('County'),
            'latitude': location.get('Latitude'),
            'longitude': location.get('Longitude'),
        }

    # =========================================================================
    # Property-specific query methods
    # =========================================================================

    def find_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Find property by address (partial match).

        Args:
            address: Address string to search for

        Returns:
            First matching property or None
        """
        address_lower = address.lower()
        for entity in self.load_all():
            prop_address = (
                entity
                .get('PropertyHeader', {})
                .get('Location', {})
                .get('Address', '')
            )
            if address_lower in prop_address.lower():
                return entity
        return None

    def find_by_zip(self, zip_code: str) -> List[Dict[str, Any]]:
        """
        Find all properties in a zip code.

        Args:
            zip_code: Zip code to filter by

        Returns:
            List of matching properties
        """
        results = []
        for entity in self.load_all():
            prop_zip = (
                entity
                .get('PropertyHeader', {})
                .get('Location', {})
                .get('ZipCode', '')
            )
            if prop_zip == zip_code:
                results.append(entity)
        return results

    def find_by_state(self, state: str) -> List[Dict[str, Any]]:
        """
        Find all properties in a state.

        Args:
            state: State abbreviation (e.g., 'FL', 'TX')

        Returns:
            List of matching properties
        """
        state_upper = state.upper()
        results = []
        for entity in self.load_all():
            prop_state = (
                entity
                .get('PropertyHeader', {})
                .get('Location', {})
                .get('State', '')
            )
            if prop_state.upper() == state_upper:
                results.append(entity)
        return results

    def find_by_county(self, county: str) -> List[Dict[str, Any]]:
        """
        Find all properties in a county.

        Args:
            county: County name to filter by

        Returns:
            List of matching properties
        """
        county_lower = county.lower()
        results = []
        for entity in self.load_all():
            prop_county = (
                entity
                .get('PropertyHeader', {})
                .get('Location', {})
                .get('County', '')
            )
            if county_lower in prop_county.lower():
                results.append(entity)
        return results

    def get_location(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Get just the location data for a property.

        Args:
            property_id: Property ID to look up

        Returns:
            Location dictionary or None
        """
        entity = self.find_by_id(property_id)
        if entity:
            return entity.get('PropertyHeader', {}).get('Location')
        return None

    def get_coordinates(self, property_id: str) -> Optional[tuple]:
        """
        Get latitude/longitude for a property.

        Args:
            property_id: Property ID to look up

        Returns:
            Tuple of (latitude, longitude) or None
        """
        location = self.get_location(property_id)
        if location:
            lat = location.get('Latitude')
            lon = location.get('Longitude')
            if lat is not None and lon is not None:
                return (lat, lon)
        return None

    def get_properties_in_radius(
        self,
        lat: float,
        lon: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """
        Find all properties within a radius of a point.

        Uses Haversine formula for distance calculation.

        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Search radius in kilometers

        Returns:
            List of properties within radius
        """
        import math

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Earth's radius in km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)

            a = (math.sin(delta_phi / 2) ** 2 +
                 math.cos(phi1) * math.cos(phi2) *
                 math.sin(delta_lambda / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            return R * c

        results = []
        for entity in self.load_all():
            coords = self.get_coordinates(self.get_entity_id(entity))
            if coords:
                prop_lat, prop_lon = coords
                distance = haversine(lat, lon, prop_lat, prop_lon)
                if distance <= radius_km:
                    results.append(entity)

        return results

    def get_total_value(self) -> float:
        """
        Calculate total property value across portfolio.

        Returns:
            Sum of all property values
        """
        total = 0.0
        for entity in self.load_all():
            value = (
                entity
                .get('PropertyHeader', {})
                .get('Valuation', {})
                .get('MarketValue', 0)
            )
            if isinstance(value, (int, float)):
                total += value
        return total

    def get_value_by_state(self) -> Dict[str, float]:
        """
        Calculate property value grouped by state.

        Returns:
            Dictionary mapping state codes to total value
        """
        values = {}
        for entity in self.load_all():
            state = (
                entity
                .get('PropertyHeader', {})
                .get('Location', {})
                .get('State', 'Unknown')
            )
            value = (
                entity
                .get('PropertyHeader', {})
                .get('Valuation', {})
                .get('MarketValue', 0)
            )
            if isinstance(value, (int, float)):
                values[state] = values.get(state, 0.0) + value
        return values
