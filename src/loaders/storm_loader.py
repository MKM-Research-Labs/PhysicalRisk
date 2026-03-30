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
Storm/Event data loader for MKM Research Labs PRS Platform.

Handles loading and querying tropical cyclone and storm event data.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class StormLoader(BaseLoader[Dict[str, Any]]):
    """
    Loader for storm/tropical cyclone event data.

    Handles storm event files with structure following tc_event_cdm.py:
    {
        "storms": [
            {
                "TCEvent": {
                    "Header": {
                        "EventID": "...",
                        "EventName": "...",
                        "Category": ...
                    },
                    "Track": [...],
                    "Impact": {...}
                }
            }
        ]
    }
    """

    ENTITY_NAME = 'storm'
    DEFAULT_FILENAME = 'storm_events.json'
    CONTAINER_KEYS = ['storms', 'events', 'tc_events', 'tropical_cyclones']

    def get_entity_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extract EventID from nested structure."""
        return (
            entity
            .get('TCEvent', {})
            .get('Header', {})
            .get('EventID')
        )

    def get_entity_summary(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create storm summary for listing."""
        tc_event = entity.get('TCEvent', {})
        header = tc_event.get('Header', {})

        return {
            'eventId': header.get('EventID'),
            'name': header.get('EventName'),
            'category': header.get('Category'),
            'basin': header.get('Basin'),
            'season': header.get('Season'),
            'startDate': header.get('StartDate'),
            'endDate': header.get('EndDate'),
            'peakIntensity': header.get('PeakIntensity'),
        }

    # =========================================================================
    # Storm-specific query methods
    # =========================================================================

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find storm by name (case-insensitive partial match).

        Args:
            name: Storm name to search for (e.g., 'Harvey', 'Katrina')

        Returns:
            First matching storm or None
        """
        name_lower = name.lower()
        for entity in self.load_all():
            storm_name = (
                entity
                .get('TCEvent', {})
                .get('Header', {})
                .get('EventName', '')
            )
            if name_lower in storm_name.lower():
                return entity
        return None

    def find_by_category(self, category: int) -> List[Dict[str, Any]]:
        """
        Find all storms of a specific category.

        Args:
            category: Saffir-Simpson category (1-5)

        Returns:
            List of matching storms
        """
        results = []
        for entity in self.load_all():
            storm_category = (
                entity
                .get('TCEvent', {})
                .get('Header', {})
                .get('Category')
            )
            if storm_category == category:
                results.append(entity)
        return results

    def find_by_season(self, season: int) -> List[Dict[str, Any]]:
        """
        Find all storms in a specific season/year.

        Args:
            season: Year (e.g., 2025)

        Returns:
            List of storms in that season
        """
        results = []
        for entity in self.load_all():
            storm_season = (
                entity
                .get('TCEvent', {})
                .get('Header', {})
                .get('Season')
            )
            if storm_season == season:
                results.append(entity)
        return results

    def find_by_basin(self, basin: str) -> List[Dict[str, Any]]:
        """
        Find all storms in a specific basin.

        Args:
            basin: Basin code (e.g., 'ATL', 'EPAC', 'WPAC')

        Returns:
            List of storms in that basin
        """
        basin_upper = basin.upper()
        results = []
        for entity in self.load_all():
            storm_basin = (
                entity
                .get('TCEvent', {})
                .get('Header', {})
                .get('Basin', '')
            )
            if storm_basin.upper() == basin_upper:
                results.append(entity)
        return results

    def get_major_hurricanes(self) -> List[Dict[str, Any]]:
        """
        Get all major hurricanes (Category 3+).

        Returns:
            List of Category 3, 4, and 5 storms
        """
        results = []
        for entity in self.load_all():
            category = (
                entity
                .get('TCEvent', {})
                .get('Header', {})
                .get('Category', 0)
            )
            if isinstance(category, int) and category >= 3:
                results.append(entity)
        return results

    def get_track(self, event_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the track points for a storm.

        Args:
            event_id: Storm event ID

        Returns:
            List of track point dictionaries or None
        """
        entity = self.find_by_id(event_id)
        if entity:
            return entity.get('TCEvent', {}).get('Track')
        return None

    def get_impact(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get impact data for a storm.

        Args:
            event_id: Storm event ID

        Returns:
            Impact dictionary or None
        """
        entity = self.find_by_id(event_id)
        if entity:
            return entity.get('TCEvent', {}).get('Impact')
        return None

    def get_storms_affecting_location(
        self,
        lat: float,
        lon: float,
        radius_km: float = 100
    ) -> List[Dict[str, Any]]:
        """
        Find storms whose track passed near a location.

        Args:
            lat: Location latitude
            lon: Location longitude
            radius_km: Search radius in kilometers

        Returns:
            List of storms that passed within radius
        """
        from .geo_utils import haversine

        results = []
        for entity in self.load_all():
            track = entity.get('TCEvent', {}).get('Track', [])
            for point in track:
                point_lat = point.get('Latitude')
                point_lon = point.get('Longitude')
                if point_lat is not None and point_lon is not None:
                    distance = haversine(lat, lon, point_lat, point_lon)
                    if distance <= radius_km:
                        results.append(entity)
                        break  # Found one point in range, move to next storm

        return results
