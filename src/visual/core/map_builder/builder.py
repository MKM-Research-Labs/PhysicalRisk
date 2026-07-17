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

"""
MapBuilder class for creating and configuring Folium maps.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

import folium

from config.visual import (
    MAP_DEFAULT_CENTER,
    MAP_DEFAULT_TILES,
    MAP_DEFAULT_ZOOM,
    get_map_center,
)
from .zoom_bounds import calculate_zoom_for_range, calculate_bounds
from .controls import MapControls

logger = logging.getLogger(__name__)


class MapBuilder:
    """
    Builder class for creating and configuring Folium maps.

    Provides methods for creating maps from coordinates or bounds,
    with configurable controls and tile layers.
    """

    # Default settings — centralised in config.visual
    DEFAULT_ZOOM   = MAP_DEFAULT_ZOOM
    DEFAULT_TILES  = MAP_DEFAULT_TILES
    DEFAULT_CENTER = MAP_DEFAULT_CENTER

    def __init__(self, tiles: str = None, default_zoom: int = None):
        """
        Initialize the map builder.

        Args:
            tiles: Tile layer name (e.g., 'OpenStreetMap', 'CartoDB positron')
            default_zoom: Default zoom level (1-18)
        """
        self.tiles = tiles or self.DEFAULT_TILES
        self.default_zoom = default_zoom or self.DEFAULT_ZOOM
        self.controls = MapControls()

    def create_map(self, center: Tuple[float, float] = None,
                   zoom: int = None,
                   coordinates: List[Tuple[float, float]] = None,
                   padding_factor: float = 1.2) -> folium.Map:
        """
        Create a Folium map.

        Can be centered explicitly or auto-calculated from coordinates.

        Args:
            center: Optional (lat, lon) center point
            zoom: Optional zoom level
            coordinates: Optional list of coordinates for auto-centering
            padding_factor: Padding multiplier for zoom calculation

        Returns:
            Configured Folium Map
        """
        # Determine center and zoom
        if center:
            map_center = center
            map_zoom = zoom or self.default_zoom
        elif coordinates:
            bounds = calculate_bounds(coordinates)
            if bounds:
                map_center = (bounds['center_lat'], bounds['center_lon'])
                max_range = max(bounds['lat_range'], bounds['lon_range'])
                map_zoom = zoom or calculate_zoom_for_range(max_range, padding_factor)
            else:
                map_center = get_map_center()
                map_zoom = self.default_zoom
        else:
            map_center = get_map_center()
            map_zoom = zoom or self.default_zoom

        # Create map
        base_map = folium.Map(
            location=list(map_center),
            zoom_start=map_zoom,
            tiles=self.tiles
        )

        # Add controls
        self.controls.apply_to_map(base_map)

        return base_map

    def create_map_from_bounds(self, min_lat: float, max_lat: float,
                               min_lon: float, max_lon: float,
                               padding_factor: float = 1.1) -> folium.Map:
        """
        Create a map fitted to explicit coordinate bounds.

        Args:
            min_lat: Southern boundary
            max_lat: Northern boundary
            min_lon: Western boundary
            max_lon: Eastern boundary
            padding_factor: Padding multiplier for zoom

        Returns:
            Folium map fitted to bounds
        """
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        max_range = max(lat_range, lon_range)

        zoom = calculate_zoom_for_range(max_range, padding_factor)

        return self.create_map(center=(center_lat, center_lon), zoom=zoom)

    def configure_controls(self, measure: bool = True, fullscreen: bool = True,
                          layer_control: bool = True, scale: bool = True):
        """
        Configure which controls to add to maps.

        Args:
            measure: Add measurement tool
            fullscreen: Add fullscreen button
            layer_control: Add layer toggle
            scale: Add scale indicator
        """
        self.controls = MapControls(
            measure=measure,
            fullscreen=fullscreen,
            layer_control=layer_control,
            scale=scale
        )

    def set_tiles(self, tiles: str):
        """Set the tile layer for new maps."""
        self.tiles = tiles

    def set_default_zoom(self, zoom: int):
        """Set the default zoom level (1-18)."""
        if 1 <= zoom <= 18:
            self.default_zoom = zoom

    def finalize_map(self, folium_map: folium.Map,
                     output_path: Union[str, Path]) -> Optional[Path]:
        """
        Finalize and save the map.

        Args:
            folium_map: Map to save
            output_path: Destination path for HTML file

        Returns:
            Path to saved file, or None on failure
        """
        try:
            # Add layer control
            self.controls.add_layer_control(folium_map)

            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save
            folium_map.save(str(output_path))

            return output_path

        except Exception as e:
            logger.error("Error saving map: %s", e)
            return None

    def add_bounds_rectangle(self, folium_map: folium.Map,
                             coordinates: List[Tuple[float, float]],
                             color: str = 'red', weight: int = 2,
                             opacity: float = 0.8, fill: bool = False,
                             fill_opacity: float = 0.1):
        """
        Add a bounding rectangle around coordinates.

        Args:
            folium_map: Map to add rectangle to
            coordinates: Coordinates to bound
            color: Line color
            weight: Line weight
            opacity: Line opacity
            fill: Whether to fill rectangle
            fill_opacity: Fill opacity
        """
        if not coordinates:
            return

        bounds = calculate_bounds(coordinates)
        if not bounds:
            return

        try:
            folium.Rectangle(
                bounds=[
                    [bounds['min_lat'], bounds['min_lon']],
                    [bounds['max_lat'], bounds['max_lon']]
                ],
                color=color,
                weight=weight,
                opacity=opacity,
                fill=fill,
                fillOpacity=fill_opacity,
                popup=f"Bounds: {len(coordinates)} points"
            ).add_to(folium_map)
        except Exception as e:
            logger.warning("Could not add bounds rectangle: %s", e)
