# Copyright (c) 2025 MKM Research Labs. All rights reserved.
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
Map building module for the visualization system.

This module provides functionality for creating and configuring the base Folium map,
including center point calculation, zoom level determination, and control setup.
"""

import folium
from folium import plugins
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union


class MapBuilder:
    """
    Builder class for creating and configuring Folium maps.
    
    This class handles the creation of base maps with appropriate center points,
    zoom levels, and standard controls for the visualization system.
    """
    
    def __init__(self):
        """Initialize the map builder with default settings."""
        self.default_zoom = 8
        self.default_tiles = 'OpenStreetMap'
        self.map_controls = {
            'measure': True,
            'fullscreen': True,
            'layer_control': True,
            'scale': True
        }
    
    def create_base_map(self, tc_data: Dict[str, Any], 
                       custom_center: Optional[Tuple[float, float]] = None,
                       custom_zoom: Optional[int] = None) -> folium.Map:
        """
        Create a base Folium map centered on the storm path.
        
        Args:
            tc_data: Tropical cyclone event timeseries data
            custom_center: Optional custom center point (lat, lon)
            custom_zoom: Optional custom zoom level
            
        Returns:
            Configured Folium Map object
        """
        if not tc_data or 'timeseries' not in tc_data:
            raise ValueError("Invalid TC data: missing timeseries")
        
        # Calculate center point and zoom
        if custom_center:
            center_lat, center_lon = custom_center
        else:
            center_lat, center_lon = self._calculate_map_center(tc_data)
        
        zoom_level = custom_zoom if custom_zoom else self._determine_zoom_level(tc_data)
        
        # Create base map
        base_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_level,
            tiles=self.default_tiles
        )
        
        # Add standard controls
        self._add_base_controls(base_map)
        
        # Add center marker for debugging (optional)
        self._add_center_marker(base_map, center_lat, center_lon)
        
        print(f"Created base map: center=({center_lat:.4f}, {center_lon:.4f}), zoom={zoom_level}")
        
        return base_map
    
    def _calculate_map_center(self, tc_data: Dict[str, Any]) -> Tuple[float, float]:
        """
        Calculate the optimal center point for the map based on storm track.
        
        Args:
            tc_data: Tropical cyclone timeseries data
            
        Returns:
            Tuple of (latitude, longitude) for map center
        """
        try:
            # Extract coordinates from timeseries
            coordinates = self._extract_coordinates(tc_data)
            
            if not coordinates:
                raise ValueError("No valid coordinates found in TC data")
            
            lats, lons = zip(*coordinates)
            
            # Calculate center using mean
            center_lat = np.mean(lats)
            center_lon = np.mean(lons)
            
            # Print diagnostic info
            print(f"Storm track analysis:")
            print(f"  Coordinates: {len(coordinates)} points")
            print(f"  Lat range: {min(lats):.4f} to {max(lats):.4f}")
            print(f"  Lon range: {min(lons):.4f} to {max(lons):.4f}")
            print(f"  Calculated center: {center_lat:.4f}°N, {center_lon:.4f}°E")
            
            return center_lat, center_lon
            
        except Exception as e:
            print(f"Error calculating map center: {e}")
            # Fallback to a default location (London area)
            return 51.5074, -0.1278
    
    def _determine_zoom_level(self, tc_data: Dict[str, Any]) -> int:
        """
        Determine appropriate zoom level based on the spatial extent of the data.
        
        Args:
            tc_data: Tropical cyclone timeseries data
            
        Returns:
            Appropriate zoom level (1-18)
        """
        try:
            coordinates = self._extract_coordinates(tc_data)
            
            if len(coordinates) < 2:
                return self.default_zoom
            
            lats, lons = zip(*coordinates)
            
            # Calculate bounding box
            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            
            # Determine zoom based on coordinate range
            max_range = max(lat_range, lon_range)
            
            if max_range > 10:
                zoom = 4
            elif max_range > 5:
                zoom = 5
            elif max_range > 2:
                zoom = 6
            elif max_range > 1:
                zoom = 7
            elif max_range > 0.5:
                zoom = 8
            elif max_range > 0.2:
                zoom = 9
            elif max_range > 0.1:
                zoom = 10
            else:
                zoom = 11
            
            print(f"Zoom calculation: range={max_range:.4f}°, zoom={zoom}")
            return zoom
            
        except Exception as e:
            print(f"Error determining zoom level: {e}")
            return self.default_zoom
    
    def _extract_coordinates(self, tc_data: Dict[str, Any]) -> List[Tuple[float, float]]:
        """
        Extract coordinate pairs from TC timeseries data.
        
        Args:
            tc_data: Tropical cyclone timeseries data
            
        Returns:
            List of (latitude, longitude) tuples
        """
        coordinates = []
        
        try:
            for ts in tc_data['timeseries']:
                ts_data = ts.get('EventTimeseries', {})
                dimensions = ts_data.get('Dimensions', {})
                
                lat = dimensions.get('lat')
                lon = dimensions.get('lon')
                
                if lat is not None and lon is not None:
                    coordinates.append((float(lat), float(lon)))
        
        except Exception as e:
            print(f"Error extracting coordinates: {e}")
        
        return coordinates
    
    def _add_base_controls(self, base_map: folium.Map):
        """
        Add standard controls to the base map.
        
        Args:
            base_map: Folium map to add controls to
        """
        try:
            # Add measurement control
            if self.map_controls.get('measure', True):
                plugins.MeasureControl(
                    position='bottomleft',
                    primary_length_unit='kilometers',
                    secondary_length_unit='miles'
                ).add_to(base_map)
            
            # Add fullscreen control
            if self.map_controls.get('fullscreen', True):
                plugins.Fullscreen(position='topleft').add_to(base_map)
            
            print("✓ Added base map controls")
            
        except Exception as e:
            print(f"Warning: Could not add some map controls: {e}")
    
    def _add_center_marker(self, base_map: folium.Map, center_lat: float, center_lon: float):
        """
        Add a center marker for debugging purposes.
        
        Args:
            base_map: Folium map to add marker to
            center_lat: Center latitude
            center_lon: Center longitude
        """
        try:
            folium.Marker(
                location=[center_lat, center_lon],
                popup=f"Map Center: {center_lat:.4f}°N, {center_lon:.4f}°E",
                tooltip="Map Center",
                icon=folium.Icon(color='black', icon='crosshairs', prefix='fa')
            ).add_to(base_map)
            
        except Exception as e:
            print(f"Warning: Could not add center marker: {e}")
    
    def add_layer_control(self, base_map: folium.Map):
        """
        Add layer control to the map.
        
        Args:
            base_map: Folium map to add layer control to
        """
        if self.map_controls.get('layer_control', True):
            try:
                folium.LayerControl().add_to(base_map)
                print("✓ Added layer control")
            except Exception as e:
                print(f"Warning: Could not add layer control: {e}")
    
    def finalize_map(self, base_map: folium.Map, output_path: Union[str, Path]) -> Optional[Path]:
        """
        Finalize the map and save it to the specified location.
        
        Args:
            base_map: Complete Folium map to save
            output_path: Path where to save the HTML file
            
        Returns:
            Path to the saved file or None if saving failed
        """
        try:
            # Add layer control if not already added
            self.add_layer_control(base_map)
            
            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the map
            base_map.save(str(output_path))
            
            print(f"✓ Map saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"✗ Error saving map: {e}")
            return None
    
    def configure_controls(self, measure: bool = True, fullscreen: bool = True, 
                          layer_control: bool = True, scale: bool = True):
        """
        Configure which controls to add to maps.
        
        Args:
            measure: Whether to add measurement control
            fullscreen: Whether to add fullscreen control
            layer_control: Whether to add layer control
            scale: Whether to add scale control
        """
        self.map_controls = {
            'measure': measure,
            'fullscreen': fullscreen,
            'layer_control': layer_control,
            'scale': scale
        }
        print(f"✓ Map controls configured: {self.map_controls}")
    
    def set_default_tiles(self, tiles: str):
        """
        Set the default tile layer for new maps.
        
        Args:
            tiles: Tile layer name (e.g., 'OpenStreetMap', 'CartoDB positron')
        """
        self.default_tiles = tiles
        print(f"✓ Default tiles set to: {tiles}")
    
    def set_default_zoom(self, zoom: int):
        """
        Set the default zoom level.
        
        Args:
            zoom: Default zoom level (1-18)
        """
        if 1 <= zoom <= 18:
            self.default_zoom = zoom
            print(f"✓ Default zoom set to: {zoom}")
        else:
            print(f"Warning: Invalid zoom level {zoom}, keeping {self.default_zoom}")
    
    def create_multi_center_map(self, coordinate_sets: List[List[Tuple[float, float]]], 
                              labels: Optional[List[str]] = None) -> folium.Map:
        """
        Create a map that encompasses multiple sets of coordinates.
        
        Args:
            coordinate_sets: List of coordinate lists to include
            labels: Optional labels for each coordinate set
            
        Returns:
            Folium map encompassing all coordinate sets
        """
        if not coordinate_sets or not any(coordinate_sets):
            raise ValueError("No coordinate sets provided")
        
        # Flatten all coordinates
        all_coords = []
        for coord_set in coordinate_sets:
            all_coords.extend(coord_set)
        
        if not all_coords:
            raise ValueError("No valid coordinates found")
        
        # Calculate bounds
        lats, lons = zip(*all_coords)
        
        # Calculate center
        center_lat = np.mean(lats)
        center_lon = np.mean(lons)
        
        # Calculate zoom based on extent
        lat_range = max(lats) - min(lats)
        lon_range = max(lons) - min(lons)
        max_range = max(lat_range, lon_range)
        
        # Add padding to the range
        padded_range = max_range * 1.2
        
        # Determine zoom
        if padded_range > 10:
            zoom = 3
        elif padded_range > 5:
            zoom = 4
        elif padded_range > 2:
            zoom = 5
        elif padded_range > 1:
            zoom = 6
        elif padded_range > 0.5:
            zoom = 7
        else:
            zoom = 8
        
        # Create map
        base_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles=self.default_tiles
        )
        
        # Add controls
        self._add_base_controls(base_map)
        
        print(f"Created multi-center map: center=({center_lat:.4f}, {center_lon:.4f}), "
              f"zoom={zoom}, coord_sets={len(coordinate_sets)}")
        
        return base_map
    
    def add_bounds_rectangle(self, base_map: folium.Map, coordinates: List[Tuple[float, float]], 
                           color: str = 'red', weight: int = 2, opacity: float = 0.8,
                           fill: bool = False, fill_opacity: float = 0.1):
        """
        Add a bounding rectangle around a set of coordinates.
        
        Args:
            base_map: Map to add rectangle to
            coordinates: List of coordinate tuples
            color: Rectangle color
            weight: Line weight
            opacity: Line opacity
            fill: Whether to fill the rectangle
            fill_opacity: Fill opacity
        """
        if not coordinates:
            return
        
        try:
            lats, lons = zip(*coordinates)
            
            # Create bounds
            bounds = [
                [min(lats), min(lons)],  # Southwest corner
                [max(lats), max(lons)]   # Northeast corner
            ]
            
            # Add rectangle
            folium.Rectangle(
                bounds=bounds,
                color=color,
                weight=weight,
                opacity=opacity,
                fill=fill,
                fillOpacity=fill_opacity,
                popup=f"Data bounds: {len(coordinates)} points"
            ).add_to(base_map)
            
            print(f"✓ Added bounds rectangle covering {len(coordinates)} points")
            
        except Exception as e:
            print(f"Warning: Could not add bounds rectangle: {e}")
    
    def create_map_from_bounds(self, min_lat: float, max_lat: float, 
                             min_lon: float, max_lon: float,
                             padding_factor: float = 0.1) -> folium.Map:
        """
        Create a map from explicit coordinate bounds.
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            padding_factor: Factor to add padding around bounds
            
        Returns:
            Folium map fitted to the bounds
        """
        # Calculate center
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        
        # Calculate extent with padding
        lat_range = (max_lat - min_lat) * (1 + padding_factor)
        lon_range = (max_lon - min_lon) * (1 + padding_factor)
        max_range = max(lat_range, lon_range)
        
        # Determine zoom
        if max_range > 20:
            zoom = 2
        elif max_range > 10:
            zoom = 3
        elif max_range > 5:
            zoom = 4
        elif max_range > 2:
            zoom = 5
        elif max_range > 1:
            zoom = 6
        elif max_range > 0.5:
            zoom = 7
        elif max_range > 0.2:
            zoom = 8
        else:
            zoom = 9
        
        # Create map
        base_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles=self.default_tiles
        )
        
        # Add controls
        self._add_base_controls(base_map)
        
        print(f"Created bounds map: bounds=({min_lat:.4f},{min_lon:.4f}) to "
              f"({max_lat:.4f},{max_lon:.4f}), zoom={zoom}")
        
        return base_map
    
    def get_map_bounds(self, coordinates: List[Tuple[float, float]]) -> Dict[str, float]:
        """
        Calculate bounding box for a set of coordinates.
        
        Args:
            coordinates: List of coordinate tuples
            
        Returns:
            Dictionary with min/max lat/lon values
        """
        if not coordinates:
            return {}
        
        lats, lons = zip(*coordinates)
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons),
            'center_lat': np.mean(lats),
            'center_lon': np.mean(lons),
            'lat_range': max(lats) - min(lats),
            'lon_range': max(lons) - min(lons)
        }