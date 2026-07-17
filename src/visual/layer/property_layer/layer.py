# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""PropertyLayer class for property risk visualization on Folium maps."""

import logging
from typing import Any, Dict, List, Optional

import folium

from config.format import property_title_py
from config.visual import PROPERTY_FLOOD_HIGH, PROPERTY_FLOOD_MEDIUM
from ...utils import ColorSchemes, DataExtractor, DataFormatter
from .popup import (create_property_popup, create_flood_risk_section,
                    create_rloan_section)
from .stats import get_property_statistics

logger = logging.getLogger(__name__)


class PropertyLayer:
    """
    Layer class for adding property markers and risk analysis to the map.

    This class handles the creation of property markers with flood risk coloring,
    mortgage status indicators, and comprehensive property information popups.
    """

    def __init__(self):
        """Initialize the property layer."""
        self.layer_name = "Properties"
        self.show_risk_colors = True
        self.show_rloan_status = True
        self.risk_based_sizing = False

    def add_to_map(self, folium_map: folium.Map, loaded_data) -> folium.FeatureGroup:
        """Add property layer to the map."""
        logger.info(f"Adding {self.layer_name} to map...")

        property_group = folium.FeatureGroup(name=self.layer_name)

        if not loaded_data.property_data:
            logger.warning("No property data available")
            return property_group

        self._property_hazard = {}
        if hasattr(loaded_data, 'property_hazard_data') and loaded_data.property_hazard_data:
            phc = loaded_data.property_hazard_data.get('property_hazard_curves', {})
            for pid, pdata in phc.items():
                if isinstance(pdata, dict):
                    self._property_hazard[pid] = pdata

        properties = self._get_properties_list(loaded_data.property_data)

        if not properties:
            logger.warning("No valid property data found")
            return property_group

        property_count = 0
        mortgaged_property_count = 0

        for prop in properties:
            try:
                property_info = DataExtractor.extract_property_info(prop)
                if property_info is None:
                    continue

                lat = property_info['coordinates']['latitude']
                lon = property_info['coordinates']['longitude']

                if lat is not None and lon is not None:
                    property_count += 1
                    property_id = property_info['property_id']

                    property_flood_info = loaded_data.property_flood_info.get(property_id, {}) if loaded_data.property_flood_info else {}
                    has_rloan = property_id in (loaded_data.rloan_lookup or {})
                    rloan_info = loaded_data.rloan_lookup.get(property_id, {}) if loaded_data.rloan_lookup else {}

                    if has_rloan:
                        mortgaged_property_count += 1

                    self._add_property_marker(property_group, property_info, property_flood_info,
                                            has_rloan, rloan_info, loaded_data)

            except Exception as e:
                logger.warning(f"Error processing property: {e}")
                continue

        property_group.add_to(folium_map)

        logger.info(f"Added {property_count} properties to map ({mortgaged_property_count} with mortgages)")
        return property_group

    def _add_property_marker(self, feature_group: folium.FeatureGroup, property_info: Dict[str, Any],
                           property_flood_info: Dict[str, Any], has_rloan: bool,
                           rloan_info: Dict[str, Any], loaded_data) -> None:
        """Add a single property marker to the feature group."""
        try:
            lat = property_info['coordinates']['latitude']
            lon = property_info['coordinates']['longitude']
            property_id = property_info['property_id']

            popup_content = self._create_property_popup(
                property_info, property_flood_info, has_rloan,
                rloan_info,
            )

            phc = self._property_hazard.get(property_id, {})
            flood_count = phc.get('flood_count', 0)
            flood_freq_label = self._get_flood_frequency_label(flood_count)
            addr = property_info.get('address', {})
            prop_address = f"{addr.get('building_number', '')} {addr.get('street_name', '')}".strip()
            prop_label = property_title_py(prop_address, property_id)
            tooltip = f"{prop_label} | Floods: {flood_count} ({flood_freq_label}){' | Mortgaged' if has_rloan else ''}"

            icon = self._get_property_icon(property_info, has_rloan)

            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=350),
                tooltip=tooltip,
                icon=icon
            )

            marker.add_to(feature_group)

        except Exception as e:
            logger.warning(f"Error creating property marker for {property_info.get('property_id', 'Unknown')}: {e}")

    def _get_property_icon(self, property_info: Dict[str, Any], has_rloan: bool) -> folium.Icon:
        """Determine the appropriate icon for a property marker."""
        property_id = property_info.get('property_id', '')
        phc = self._property_hazard.get(property_id, {}) if hasattr(self, '_property_hazard') else {}
        flood_count = phc.get('flood_count', 0)

        if flood_count > PROPERTY_FLOOD_HIGH:
            color = 'red'
        elif flood_count >= PROPERTY_FLOOD_MEDIUM:
            color = 'orange'
        else:
            color = 'green'

        if self.show_rloan_status and has_rloan:
            icon_type = 'university'
        else:
            icon_type = 'home'

        return folium.Icon(color=color, icon=icon_type, prefix='fa')

    @staticmethod
    def _get_flood_frequency_label(flood_count: int) -> str:
        """Get RAG label for flood frequency from simulated storms."""
        if flood_count > PROPERTY_FLOOD_HIGH:
            return "High"
        elif flood_count >= PROPERTY_FLOOD_MEDIUM:
            return "Medium"
        else:
            return "Low"

    @staticmethod
    def _get_properties_list(property_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract properties list from property data."""
        from visual.layer import get_properties_list
        return get_properties_list(property_data)

    def configure(self, show_risk_colors: bool = True, show_rloan_status: bool = True,
                 risk_based_sizing: bool = False):
        """Configure property layer display options."""
        self.show_risk_colors = show_risk_colors
        self.show_rloan_status = show_rloan_status
        self.risk_based_sizing = risk_based_sizing

        logger.info(f"Property layer configured: risk_colors={show_risk_colors}, mortgage={show_rloan_status}, sizing={risk_based_sizing}")

    # -----------------------------------------------------------------------
    # Delegators to popup submodule (backward-compatible instance methods)
    # -----------------------------------------------------------------------

    def _create_property_popup(self, property_info, property_flood_info,
                                has_rloan, rloan_info) -> str:
        """Create detailed popup content for a property marker."""
        return create_property_popup(property_info, property_flood_info,
                                     has_rloan, rloan_info)

    def _create_flood_risk_section(self, property_flood_info) -> str:
        """Create the flood risk information section."""
        return create_flood_risk_section(property_flood_info)

    def _create_rloan_section(self, rloan_info, property_value) -> str:
        """Create the mortgage information section."""
        return create_rloan_section(rloan_info, property_value)

    def get_property_statistics(self, properties: List[Dict[str, Any]], loaded_data) -> Dict[str, Any]:
        """Calculate statistics for the properties."""
        return get_property_statistics(properties, loaded_data)
