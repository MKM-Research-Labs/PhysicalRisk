# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""MortgageLayer class for mortgage risk visualization on Folium maps."""

import logging
from typing import Any, Dict, List

import folium

from .circles import add_ltv_indicators, add_mortgage_risk_circles, get_mortgage_risk_color
from .popup import create_mortgage_circle_popup
from .stats import get_mortgage_statistics

logger = logging.getLogger(__name__)


class MortgageLayer:
    """
    Layer class for adding mortgage risk visualization overlays to the map.

    This class handles the creation of mortgage risk circles, LTV indicators,
    and financial risk visualization elements.
    """

    def __init__(self):
        """Initialize the mortgage layer."""
        self.layer_name = "Mortgage Risk"
        self.show_risk_circles = True
        self.show_ltv_indicators = True
        self.circle_opacity = 0.4
        self.max_circle_radius = 500  # meters

    def add_to_map(self, folium_map: folium.Map, loaded_data) -> folium.FeatureGroup:
        """
        Add mortgage layer to the map.

        Args:
            folium_map: The Folium map to add the layer to
            loaded_data: LoadedData container with all data

        Returns:
            FeatureGroup containing all mortgage elements
        """
        logger.info(f"Adding {self.layer_name} to map...")

        mortgage_group = folium.FeatureGroup(name=self.layer_name)

        if not loaded_data.mortgage_data or not loaded_data.property_data:
            logger.warning("Insufficient data for mortgage layer (need both mortgage and property data)")
            return mortgage_group

        mortgage_locations = self._extract_mortgage_locations(loaded_data)

        if not mortgage_locations:
            logger.warning("No valid mortgage location data found")
            return mortgage_group

        if self.show_risk_circles:
            add_mortgage_risk_circles(mortgage_group, mortgage_locations,
                                      self.circle_opacity, self.max_circle_radius)

        if self.show_ltv_indicators:
            add_ltv_indicators(mortgage_group, mortgage_locations)

        mortgage_group.add_to(folium_map)

        logger.info(f"Added {len(mortgage_locations)} mortgage risk indicators to map")
        return mortgage_group

    def _extract_mortgage_locations(self, loaded_data) -> List[Dict[str, Any]]:
        """Extract mortgage information combined with property locations."""
        mortgage_locations = []

        if not loaded_data.mortgage_lookup:
            return mortgage_locations

        properties = self._get_properties_list(loaded_data.property_data)
        property_coords = {}

        for prop in properties:
            try:
                header = prop.get('PropertyHeader', {}).get('Header', {})
                property_id = header.get('PropertyID')
                location = prop.get('PropertyHeader', {}).get('Location', {})
                lat = location.get('LatitudeDegrees') or location.get('Latitude')
                lon = location.get('LongitudeDegrees') or location.get('Longitude')

                if property_id and lat is not None and lon is not None:
                    property_coords[property_id] = {'lat': float(lat), 'lon': float(lon)}
            except Exception:
                continue

        for property_id, mortgage_info in loaded_data.mortgage_lookup.items():
            if property_id in property_coords:
                try:
                    mortgage_risk_info = None
                    if loaded_data.mortgage_risk_info and 'by_property_id' in loaded_data.mortgage_risk_info:
                        mortgage_risk_info = loaded_data.mortgage_risk_info['by_property_id'].get(property_id)

                    property_flood_info = loaded_data.property_flood_info.get(property_id, {}) if loaded_data.property_flood_info else {}

                    mortgage_locations.append({
                        'property_id': property_id,
                        'lat': property_coords[property_id]['lat'],
                        'lon': property_coords[property_id]['lon'],
                        'mortgage_info': mortgage_info,
                        'mortgage_risk_info': mortgage_risk_info,
                        'property_flood_info': property_flood_info
                    })

                except Exception as e:
                    logger.warning(f"Error processing mortgage for property {property_id}: {e}")
                    continue

        return mortgage_locations

    def _get_properties_list(self, property_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract properties list from property data."""
        if isinstance(property_data, dict):
            properties = property_data.get('items') or property_data.get('properties') or []
            if not properties and 'PropertyHeader' in property_data:
                properties = [property_data]
            elif not properties:
                properties = property_data.get('portfolio', [])
        elif isinstance(property_data, list):
            properties = property_data
        else:
            properties = []

        return properties

    def configure(self, show_risk_circles: bool = True, show_ltv_indicators: bool = True,
                 circle_opacity: float = 0.4, max_circle_radius: int = 500):
        """Configure mortgage layer display options."""
        self.show_risk_circles = show_risk_circles
        self.show_ltv_indicators = show_ltv_indicators
        self.circle_opacity = circle_opacity
        self.max_circle_radius = max_circle_radius

        logger.info(f"Mortgage layer configured: circles={show_risk_circles}, ltv={show_ltv_indicators}, "
              f"opacity={circle_opacity}, max_radius={max_circle_radius}")

    def get_mortgage_statistics(self, mortgage_locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for mortgages."""
        return get_mortgage_statistics(mortgage_locations)

    def _get_mortgage_risk_color(self, mortgage_info, mortgage_risk_info, property_flood_info) -> str:
        """Determine color for a mortgage risk circle."""
        return get_mortgage_risk_color(mortgage_info, mortgage_risk_info, property_flood_info)

    def _create_mortgage_circle_popup(self, location: Dict[str, Any]) -> str:
        """Create popup HTML for a mortgage risk circle."""
        return create_mortgage_circle_popup(location)

    def _add_mortgage_risk_circles(self, feature_group, mortgage_locations):
        """Add mortgage risk circles (delegates to circles module)."""
        add_mortgage_risk_circles(feature_group, mortgage_locations,
                                  self.circle_opacity, self.max_circle_radius)

    def _add_ltv_indicators(self, feature_group, mortgage_locations):
        """Add LTV indicators (delegates to circles module)."""
        add_ltv_indicators(feature_group, mortgage_locations)
