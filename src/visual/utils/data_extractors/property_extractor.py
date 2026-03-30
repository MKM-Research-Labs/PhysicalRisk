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

"""Property data extraction utilities."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


def extract_property_info(prop: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract property information from the given property data.

    Args:
        prop: The property data dictionary

    Returns:
        Dictionary containing extracted property information or None if extraction fails
    """
    try:
        # Extract header information
        header = prop.get('PropertyHeader', {}).get('Header', {})
        property_id = header.get('PropertyID', 'Unknown')
        property_type = header.get('propertyType', 'Unknown')
        property_status = header.get('propertyStatus', 'Unknown')

        # Extract property attributes
        property_attrs = prop.get('PropertyHeader', {}).get('PropertyAttributes', {})
        building_type = property_attrs.get('PropertyType', 'Unknown')
        construction_year = property_attrs.get('ConstructionYear', 'Unknown')
        number_of_storeys = property_attrs.get('NumberOfStoreys', 'Unknown')

        # Extract construction information
        construction = prop.get('PropertyHeader', {}).get('Construction', {})
        construction_type = construction.get('ConstructionType', 'Unknown')

        # Extract location information - try multiple possible field names
        location = prop.get('PropertyHeader', {}).get('Location', {})
        lat = location.get('LatitudeDegrees') or location.get('Latitude')
        lon = location.get('LongitudeDegrees') or location.get('Longitude')

        # Validate coordinates
        if lat is None or lon is None:
            logger.warning("Invalid coordinates for property %s", property_id)
            return None

        # Extract address components
        building_number = location.get('BuildingNumber', '')
        street_name = location.get('StreetName', '')
        town_city = location.get('TownCity', '')
        post_code = location.get('Postcode', '')

        # Extract risk and value information
        flood_risk = prop.get('FloodRisk', 'Unknown')
        thames_proximity = prop.get('ThamesProximity', 'Unknown')
        ground_elevation = prop.get('GroundElevation', 'Unknown')
        elevation_estimated = prop.get('ElevationEstimated', False)

        # Extract additional CDM fields
        location = prop.get('PropertyHeader', {}).get('Location', {})
        risk_assessment = location.get('RiskAssessment', prop.get('PropertyHeader', {}).get('RiskAssessment', {}))
        floor_level_m = construction.get('FloorLevelMeters', 'N/A')
        flood_zone = risk_assessment.get('EAFloodZone', 'N/A')
        river_distance_m = risk_assessment.get('RiverDistanceMeters', 'N/A')

        # Try multiple paths for property value
        property_value = _extract_property_value(prop)

        # Construct the extracted information dictionary
        extracted_info = {
            'property_id': property_id,
            'property_type': property_type,
            'property_status': property_status,
            'building_type': building_type,
            'construction_year': construction_year,
            'number_of_storeys': number_of_storeys,
            'construction_type': construction_type,
            'coordinates': {'latitude': lat, 'longitude': lon},
            'address': {
                'building_number': building_number,
                'street_name': street_name,
                'town_city': town_city,
                'post_code': post_code
            },
            'flood_risk': flood_risk,
            'thames_proximity': thames_proximity,
            'ground_elevation': ground_elevation,
            'elevation_estimated': elevation_estimated,
            'floor_level_m': floor_level_m,
            'flood_zone': flood_zone,
            'river_distance_m': river_distance_m,
            'property_value': property_value,
            'property_age_factor': _calculate_age_factor(construction_year)
        }

        return extracted_info

    except Exception as e:
        logger.error("Error extracting property info for %s: %s", prop.get('PropertyHeader', {}).get('Header', {}).get('PropertyID', 'Unknown'), e)
        return None


def _extract_property_value(prop: Dict[str, Any]) -> Any:
    """Extract property value from various possible locations in the data."""
    value_paths = [
        ['PropertyValue'],
        ['PropertyHeader', 'Valuation', 'PropertyValue'],
        ['Valuation', 'PropertyValue'],
        ['PropertyHeader', 'PropertyValue']
    ]

    for path in value_paths:
        current = prop
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                current = None
                break

        if current is not None and current != 'Unknown':
            return current

    return 'Unknown'


def _calculate_age_factor(construction_year: Union[int, str]) -> str:
    """Calculate property age factor.

    Delegates to PropertyFormatters.format_property_age.
    """
    from visual.utils.formatters import DataFormatter
    return DataFormatter.format_property_age(construction_year)


class PropertyDataExtractor:
    """
    Specialized extractor for property data.

    This class provides a more specific interface for property data extraction
    while maintaining compatibility with the test expectations.
    """

    def extract_property_info(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract property information from property data.

        Args:
            property_data: Raw property data dictionary

        Returns:
            Extracted property information or None if extraction fails
        """
        return extract_property_info(property_data)

    def extract_coordinates(self, property_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Extract just the coordinates from property data.

        Args:
            property_data: Raw property data dictionary

        Returns:
            Dictionary with latitude and longitude or None
        """
        info = self.extract_property_info(property_data)
        if info and 'coordinates' in info:
            return info['coordinates']
        return None

    def extract_address(self, property_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract address information from property data.

        Args:
            property_data: Raw property data dictionary

        Returns:
            Dictionary with address components or None
        """
        info = self.extract_property_info(property_data)
        if info and 'address' in info:
            return info['address']
        return None
