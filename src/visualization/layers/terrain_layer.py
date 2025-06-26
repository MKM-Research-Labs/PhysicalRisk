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
Property layer module for property visualization.

This module provides functionality for adding property markers with
risk indicators, mortgage status, and detailed analysis popups.
"""

#!/usr/bin/env python3
"""
Terrain layer module for terrain visualization.

This module provides functionality for adding terrain elevation overlays,
Thames river features, and topographical analysis.
"""

#!/usr/bin/env python3
"""
Terrain layer module for terrain visualization.

This module provides functionality for adding terrain elevation overlays,
Thames river features, and topographical analysis.
"""

import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import folium

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths
from src.utilities.elevation import THAMES_POINTS

from src.visualization.utils import ColorSchemes, DataFormatter, DataExtractor, RiskAssessor

THAMES_LOCATIONS_AVAILABLE = len(THAMES_POINTS) > 0

class TerrainLayer:
    """
    Thames Valley terrain visualization layer.
    
    This class provides terrain visualization capabilities that can be integrated
    into the main visualization system. It handles DEM data loading, terrain 
    colorization, and interactive terrain features.
    """
    
    def __init__(self, input_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the terrain layer.
        
        Args:
            input_dir: Directory containing DEM files (defaults to project_root/input)
        """
        # From layers/terrain_layer.py, project root is 4 levels up
        # layers/ -> visualization/ -> src/ -> root/
        self.project_root = current_file.parent.parent.parent.parent
        
        # Set input directory
        if input_dir is None:
            self.input_dir = self.project_root / "input"
        else:
            self.input_dir = Path(input_dir)
        
        # Terrain data storage
        self.terrain_data = None
        self.terrain_bounds = None
        self.dem_loaded = False
        
        # Terrain visualization parameters
        self.TARGET_RIVER_MIN = 3.9
        self.TARGET_RIVER_MAX = 13.8
        
        # Color scheme configuration
        self.terrain_colors = {
            'river': [0, 100, 255],        # Blue
            'floodplain': [0, 200, 50],    # Green  
            'terraces': [100, 200, 0],     # Yellow-green
            'hills': [150, 100, 50]        # Brown
        }
        
        print(f"🏔️ TerrainLayer initialized")
        print(f"   Project root: {self.project_root}")
        print(f"   Input directory: {self.input_dir}")
        print(f"   Thames locations available: {THAMES_LOCATIONS_AVAILABLE}")
        if THAMES_LOCATIONS_AVAILABLE:
            print(f"   Thames points loaded: {len(THAMES_POINTS)} gauge locations")
    
    def load_terrain_data(self, dem_filename: str = "thames_dem.asc") -> bool:
        """
        Load terrain data from DEM file.
        
        Args:
            dem_filename: Name of the DEM file to load
            
        Returns:
            True if successful, False otherwise
        """
        dem_path = self.input_dir / dem_filename
        
        if not dem_path.exists():
            print(f"⚠️  DEM file not found: {dem_path}")
            print(f"   Expected location: {self.input_dir}/thames_dem.asc")
            print(f"   Try running terrain.py first to generate the DEM")
            print(f"   Or check if the file exists in root/input/")
            return False
        
        try:
            print(f"📖 Loading terrain data from: {dem_path}")
            
            # Load ESRI ASCII grid format
            self.terrain_data, self.terrain_bounds = self._load_ascii_grid(dem_path)
            
            if self.terrain_data is not None:
                self.dem_loaded = True
                print(f"✅ Terrain data loaded successfully")
                print(f"   Data shape: {self.terrain_data.shape}")
                print(f"   Elevation range: {self.terrain_data.min():.1f} to {self.terrain_data.max():.1f}m")
                print(f"   Bounds: {self.terrain_bounds}")
                return True
            else:
                print(f"❌ Failed to load terrain data")
                return False
                
        except Exception as e:
            print(f"❌ Error loading terrain data: {e}")
            return False
    
    def _load_ascii_grid(self, file_path: Path) -> Tuple[Optional[np.ndarray], Optional[Tuple[float, float, float, float]]]:
        """
        Load ESRI ASCII grid format.
        
        Args:
            file_path: Path to the ASCII grid file
            
        Returns:
            Tuple of (data_array, bounds) or (None, None) if failed
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse header
            header = {}
            data_start_line = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line[0].isdigit() and '-' not in line[0]:
                    parts = line.split()
                    if len(parts) >= 2:
                        header[parts[0].lower()] = float(parts[1])
                        data_start_line = i + 1
                else:
                    break
            
            # Extract grid parameters
            ncols = int(header.get('ncols', 0))
            nrows = int(header.get('nrows', 0))
            xllcorner = header.get('xllcorner', 0.0)
            yllcorner = header.get('yllcorner', 0.0)
            cellsize = header.get('cellsize', 1.0)
            nodata_value = header.get('nodata_value', -9999)
            
            print(f"   Grid parameters: {ncols}x{nrows}, cellsize={cellsize}")
            
            # Load data
            data = []
            for line in lines[data_start_line:]:
                line = line.strip()
                if line:
                    row_data = [float(x) for x in line.split()]
                    data.append(row_data)
            
            # Convert to numpy array and flip (ASCII grid is top-to-bottom, we want bottom-to-top)
            data_array = np.array(data)
            data_array = np.flipud(data_array)  # Flip vertically
            
            # Replace nodata values with NaN
            data_array[data_array == nodata_value] = np.nan
            
            # Calculate bounds (min_lon, min_lat, max_lon, max_lat)
            bounds = (
                xllcorner,                          # min_lon
                yllcorner,                          # min_lat  
                xllcorner + ncols * cellsize,       # max_lon
                yllcorner + nrows * cellsize        # max_lat
            )
            
            return data_array, bounds
            
        except Exception as e:
            print(f"Error parsing ASCII grid: {e}")
            return None, None
    
    def add_to_map(self, folium_map, opacity: float = 0.7, 
                   show_thames_points: bool = True,
                   show_elevation_legend: bool = True) -> Optional[folium.FeatureGroup]:
        """
        Add terrain layer to a Folium map.
        
        Args:
            folium_map: Folium map to add terrain to
            opacity: Terrain overlay opacity (0.0 to 1.0)
            show_thames_points: Whether to show Thames gauge points
            show_elevation_legend: Whether to show elevation legend
            
        Returns:
            FeatureGroup containing terrain elements or None if failed
        """
        if not self.dem_loaded or self.terrain_data is None:
            print("⚠️  No terrain data loaded. Call load_terrain_data() first.")
            return None
        
        try:
            print(f"🗺️ Adding terrain layer to map...")
            
            # Create feature group for terrain elements
            terrain_group = folium.FeatureGroup(name="Thames Valley Terrain")
            
            # Add terrain overlay
            self._add_terrain_overlay(terrain_group, opacity)
            
            # Add Thames river line and points if available
            if show_thames_points and THAMES_LOCATIONS_AVAILABLE:
                self._add_thames_features(terrain_group)
            
            # Add elevation legend
            if show_elevation_legend:
                self._add_elevation_legend(folium_map)
            
            # Add terrain group to map
            terrain_group.add_to(folium_map)
            
            print(f"✅ Terrain layer added successfully")
            return terrain_group
            
        except Exception as e:
            print(f"❌ Error adding terrain layer: {e}")
            return None
    
    def _add_terrain_overlay(self, feature_group, opacity: float):
        """
        Add terrain elevation overlay to the feature group.
        
        Args:
            feature_group: Folium FeatureGroup to add overlay to
            opacity: Overlay opacity
        """
        print(f"   Adding terrain elevation overlay...")
        
        # Create RGB array for terrain visualization
        rgb_array = self._create_terrain_rgb()
        
        # Add as image overlay
        min_lon, min_lat, max_lon, max_lat = self.terrain_bounds
        
        folium.raster_layers.ImageOverlay(
            rgb_array,
            bounds=[[min_lat, min_lon], [max_lat, max_lon]],
            name='Thames Valley Elevation',
            opacity=opacity
        ).add_to(feature_group)
        
        print(f"   ✅ Elevation overlay added (opacity: {opacity})")
    
    def _create_terrain_rgb(self) -> np.ndarray:
        """
        Create RGB color array for terrain visualization.
        
        Returns:
            RGB array for terrain visualization
        """
        rgb_array = np.zeros((self.terrain_data.shape[0], self.terrain_data.shape[1], 3), dtype=np.uint8)
        
        # Color scheme: Blue (river) -> Green (floodplain) -> Yellow-green (terraces) -> Brown (hills)
        for i in range(self.terrain_data.shape[0]):
            for j in range(self.terrain_data.shape[1]):
                elevation = self.terrain_data[i, j]
                
                # Handle NaN values
                if np.isnan(elevation):
                    rgb_array[i, j] = [0, 0, 0]  # Black for nodata
                elif elevation < self.TARGET_RIVER_MAX + 2:  # River/low areas
                    rgb_array[i, j] = self.terrain_colors['river']
                elif elevation < self.TARGET_RIVER_MAX + 10:  # Floodplain
                    rgb_array[i, j] = self.terrain_colors['floodplain']
                elif elevation < self.TARGET_RIVER_MAX + 20:  # Terraces
                    rgb_array[i, j] = self.terrain_colors['terraces']
                else:  # Hills
                    rgb_array[i, j] = self.terrain_colors['hills']
        
        return rgb_array
    
    def _add_thames_features(self, feature_group):
        """
        Add Thames river line and gauge points to the feature group.
        
        Args:
            feature_group: Folium FeatureGroup to add Thames features to
        """
        print(f"   Adding Thames river features...")
        
        # Add Thames river line - only take first 2 values (lat, lon)
        thames_coordinates = [[point[0], point[1]] for point in THAMES_POINTS]
        folium.PolyLine(
            locations=thames_coordinates,
            color='blue',
            weight=3,
            opacity=0.8,
            popup='Thames River (Flows West → East)',
            tooltip='Thames River - Gauge Network'
        ).add_to(feature_group)
        
        # Add individual Thames gauge points
        for i, point in enumerate(THAMES_POINTS):
            lat, lon = point[0], point[1]  # Explicitly take first 2 values
            self._add_thames_point_marker(feature_group, i, lat, lon)
        
    print(f"   ✅ Added Thames river line and {len(THAMES_POINTS)} gauge points")
    
    
    def _add_thames_point_marker(self, feature_group, index: int, lat: float, lon: float):
        """
        Add individual Thames gauge point marker.
        
        Args:
            feature_group: Folium FeatureGroup to add marker to
            index: Point index
            lat: Latitude
            lon: Longitude
        """
        # Get elevation at this point if available
        elevation_text = ""
        if self.dem_loaded and self.terrain_data is not None:
            elevation = self._get_elevation_at_point(lat, lon)
            if elevation is not None:
                elevation_text = f" | Elevation: {elevation:.1f}m"
        
        # Different styling for start, end, and regular points
        if index == 0:
            # Start point (west)
            icon = folium.Icon(color='green', icon='play', prefix='fa')
            popup_text = f'Thames Gauge {index}: START (West)\nLat: {lat:.4f}, Lon: {lon:.4f}{elevation_text}'
        elif index == len(THAMES_POINTS) - 1:
            # End point (east)
            icon = folium.Icon(color='red', icon='stop', prefix='fa')
            popup_text = f'Thames Gauge {index}: END (East)\nLat: {lat:.4f}, Lon: {lon:.4f}{elevation_text}'
        elif index % 5 == 0:
            # Every 5th point - reference marker
            icon = folium.Icon(color='blue', icon='tint', prefix='fa')
            popup_text = f'Thames Gauge {index}\nLat: {lat:.4f}, Lon: {lon:.4f}{elevation_text}'
        else:
            # Regular points - small circle markers
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                popup=f'Thames Gauge {index}\nLat: {lat:.4f}, Lon: {lon:.4f}{elevation_text}',
                tooltip=f'Gauge {index}{elevation_text}',
                color='lightblue',
                fill=True,
                fillColor='lightblue',
                fillOpacity=0.7
            ).add_to(feature_group)
            return
        
        # Add marker for special points
        folium.Marker(
            location=[lat, lon],
            popup=popup_text,
            tooltip=f'Thames Gauge {index}{elevation_text}',
            icon=icon
        ).add_to(feature_group)
    
    def _get_elevation_at_point(self, lat: float, lon: float) -> Optional[float]:
        """
        Get elevation at specific coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Elevation in meters or None if not available
        """
        if not self.dem_loaded or self.terrain_data is None or self.terrain_bounds is None:
            return None
        
        try:
            min_lon, min_lat, max_lon, max_lat = self.terrain_bounds
            
            # Check if point is within bounds
            if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
                return None
            
            # Calculate grid indices
            nrows, ncols = self.terrain_data.shape
            cellsize_lon = (max_lon - min_lon) / ncols
            cellsize_lat = (max_lat - min_lat) / nrows
            
            col_idx = int((lon - min_lon) / cellsize_lon)
            row_idx = int((lat - min_lat) / cellsize_lat)
            
            # Clamp to valid indices
            col_idx = max(0, min(col_idx, ncols - 1))
            row_idx = max(0, min(row_idx, nrows - 1))
            
            elevation = self.terrain_data[row_idx, col_idx]
            
            # Return None for NaN values
            if np.isnan(elevation):
                return None
            
            return float(elevation)
            
        except Exception:
            return None
    
    def _add_elevation_legend(self, folium_map):
        """
        Add elevation legend to the map.
        
        Args:
            folium_map: Folium map to add legend to
        """
        legend_html = f'''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 300px; height: 280px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);">
        <h4 style="margin-top: 0;">Thames Valley Terrain</h4>
        <p><span style="color:rgb(0,100,255); font-weight:bold;">■</span> River ({self.TARGET_RIVER_MIN:.1f}-{self.TARGET_RIVER_MAX:.1f}m)</p>
        <p><span style="color:rgb(0,200,50); font-weight:bold;">■</span> Floodplain (~{self.TARGET_RIVER_MAX + 5:.0f}m)</p>
        <p><span style="color:rgb(100,200,0); font-weight:bold;">■</span> Terraces (~{self.TARGET_RIVER_MAX + 15:.0f}m)</p>
        <p><span style="color:rgb(150,100,50); font-weight:bold;">■</span> Hills (>{self.TARGET_RIVER_MAX + 20:.0f}m)</p>
        <hr style="margin: 8px 0;">
        '''
        
        if THAMES_LOCATIONS_AVAILABLE:
            legend_html += f'''
            <p><strong>Thames Gauges ({len(THAMES_POINTS)} total):</strong></p>
            <p style="font-size: 12px; margin: 2px 0;">🟢 START (West) | 🔵 Reference | 🔴 END (East)</p>
            <p style="font-size: 12px; margin: 2px 0;">💙 Individual gauge locations</p>
            <p><strong>Flow Direction: West ➜ East</strong></p>
            '''
        
        legend_html += f'''
        <p style="font-size: 11px; color: #666; margin-top: 8px;">
        Data: Physics-based DEM with REM normalization<br>
        Generated by Thames Valley Terrain Generator
        </p>
        </div>
        '''
        
        folium_map.get_root().html.add_child(folium.Element(legend_html))
        print(f"   ✅ Elevation legend added")
    
    def get_terrain_statistics(self) -> Dict[str, Any]:
        """
        Get terrain data statistics.
        
        Returns:
            Dictionary with terrain statistics
        """
        if not self.dem_loaded or self.terrain_data is None:
            return {'loaded': False, 'error': 'No terrain data loaded'}
        
        # Calculate statistics
        valid_data = self.terrain_data[~np.isnan(self.terrain_data)]
        
        stats = {
            'loaded': True,
            'shape': self.terrain_data.shape,
            'bounds': self.terrain_bounds,
            'elevation': {
                'min': float(valid_data.min()),
                'max': float(valid_data.max()),
                'mean': float(valid_data.mean()),
                'std': float(valid_data.std())
            },
            'data_coverage': {
                'total_cells': self.terrain_data.size,
                'valid_cells': len(valid_data),
                'coverage_percent': (len(valid_data) / self.terrain_data.size) * 100
            },
            'thames_features': {
                'available': THAMES_LOCATIONS_AVAILABLE,
                'gauge_count': len(THAMES_POINTS) if THAMES_LOCATIONS_AVAILABLE else 0
            }
        }
        
        return stats
    
    def configure_colors(self, color_scheme: Dict[str, List[int]]):
        """
        Configure terrain color scheme.
        
        Args:
            color_scheme: Dictionary with color definitions
                         Keys: 'river', 'floodplain', 'terraces', 'hills'
                         Values: [R, G, B] lists
        """
        for terrain_type, color in color_scheme.items():
            if terrain_type in self.terrain_colors:
                self.terrain_colors[terrain_type] = color
                print(f"✅ Updated {terrain_type} color to RGB{color}")
            else:
                print(f"⚠️  Unknown terrain type: {terrain_type}")
    
    def export_terrain_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Export terrain bounds for use by other layers.
        
        Returns:
            Bounds tuple (min_lon, min_lat, max_lon, max_lat) or None
        """
        return self.terrain_bounds if self.dem_loaded else None
    
    def create_standalone_terrain_map(self, output_filename: str = "terrain_standalone.html",
                                    center_coords: Optional[Tuple[float, float]] = None,
                                    zoom: int = 10) -> Optional[Path]:
        """
        Create a standalone terrain map (useful for testing).
        
        Args:
            output_filename: Output HTML filename
            center_coords: Map center coordinates (lat, lon)
            zoom: Initial zoom level
            
        Returns:
            Path to created map or None if failed
        """
        if not self.dem_loaded:
            print("⚠️  No terrain data loaded for standalone map")
            return None
        
        try:
            print(f"🗺️ Creating standalone terrain map...")
            
            # Determine center coordinates
            if center_coords is None:
                if THAMES_LOCATIONS_AVAILABLE and THAMES_POINTS:
                    river_pts = np.array(THAMES_POINTS)
                    center_lat = float(np.mean(river_pts[:, 0]))
                    center_lon = float(np.mean(river_pts[:, 1]))
                else:
                    # Use terrain bounds center
                    min_lon, min_lat, max_lon, max_lat = self.terrain_bounds
                    center_lat = (min_lat + max_lat) / 2
                    center_lon = (min_lon + max_lon) / 2
            else:
                center_lat, center_lon = center_coords
            
            # Create base map with matching tiles
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=11,
                tiles=None  # Start with no tiles
            )
            terrain_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles=None
)
            
            # Add OpenStreetMap tile layer with specific settings
            folium.TileLayer(
                tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                attr='© OpenStreetMap contributors',
                name='OpenStreetMap',
                overlay=False,
                control=True
            ).add_to(terrain_map)
            
            # Add terrain layer
            terrain_group = self.add_to_map(terrain_map)
            
            if terrain_group is None:
                print("❌ Failed to add terrain layer to standalone map")
                return None
            
            # Add layer control
            folium.LayerControl().add_to(terrain_map)
            
            # Save map
            output_path = self.input_dir / output_filename
            terrain_map.save(str(output_path))
            
            print(f"✅ Standalone terrain map created: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error creating standalone terrain map: {e}")
            return None


# Convenience function for quick terrain layer usage
def create_terrain_layer(input_dir: Optional[Union[str, Path]] = None,
                        dem_filename: str = "thames_dem.asc") -> Optional[TerrainLayer]:
    """
    Create and initialize a terrain layer.
    
    Args:
        input_dir: Directory containing DEM files
        dem_filename: DEM filename to load
        
    Returns:
        Initialized TerrainLayer or None if failed
    """
    try:
        terrain = TerrainLayer(input_dir)
        
        if terrain.load_terrain_data(dem_filename):
            return terrain
        else:
            print(f"⚠️  Failed to load terrain data from {dem_filename}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating terrain layer: {e}")
        return None


# Demo function
def demo_terrain_layer():
    """Demonstrate terrain layer functionality."""
    print("🏔️ Thames Valley Terrain Layer Demo")
    print("=" * 50)
    
    # Create terrain layer
    terrain = create_terrain_layer()
    
    if terrain is None:
        print("❌ Failed to create terrain layer")
        print("   Make sure thames_dem.asc exists in the input directory")
        print("   Run terrain.py first to generate the DEM")
        return
    
    # Show statistics
    stats = terrain.get_terrain_statistics()
    print(f"\n📊 Terrain Statistics:")
    print(f"   Shape: {stats['shape']}")
    print(f"   Elevation range: {stats['elevation']['min']:.1f} to {stats['elevation']['max']:.1f}m")
    print(f"   Coverage: {stats['data_coverage']['coverage_percent']:.1f}%")
    print(f"   Thames gauges: {stats['thames_features']['gauge_count']}")
    
    # Create standalone map
    map_path = terrain.create_standalone_terrain_map("terrain_demo.html")
    
    if map_path:
        print(f"\n✅ Demo terrain map created: {map_path}")
        print("   Open in browser to view the terrain visualization")
    else:
        print("❌ Failed to create demo map")


if __name__ == "__main__":
    demo_terrain_layer()