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
Storm layer module for tropical cyclone visualization.

This module provides functionality for adding storm paths, markers, and
cyclone-specific visualizations to the map.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import folium
import numpy as np
import colorsys

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths

# Import utils
try:
    from ..utils import ColorSchemes, DataFormatter
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(current_file.parent.parent))
    from utils import ColorSchemes, DataFormatter


class StormLayer:
    """
    Layer class for adding tropical cyclone storm paths and related visualizations.
    
    This class handles the creation of storm track lines, time-based markers,
    storm size circles, and intensity indicators.
    """
    
    def __init__(self):
        """Initialize the storm layer."""
        self.layer_name = "Storm Path"
        self.show_storm_size = True
        self.show_time_markers = True
        self.marker_interval = 2  # Every 1 hours with 30-min intervals
        self.color_scheme = "wind_speed"  # or "pressure", "time"
    
    def add_to_map(self, folium_map: folium.Map, tc_data: Dict[str, Any]) -> folium.FeatureGroup:
        """
        Add storm layer to the map.
        
        Args:
            folium_map: The Folium map to add the layer to
            tc_data: Tropical cyclone timeseries data
            
        Returns:
            FeatureGroup containing all storm elements
        """
        print(f"Adding {self.layer_name} to map...")
        
        # Create feature group for storm elements
        storm_group = folium.FeatureGroup(name=self.layer_name)
        
        # Extract storm track coordinates and data
        storm_data = self._extract_storm_data(tc_data)
        
        if not storm_data:
            print("⚠️  No valid storm data found")
            return storm_group
        
        # Add storm path
        self._add_storm_path(storm_group, storm_data)
        
        # Add storm size circles
        if self.show_storm_size:
            self._add_storm_size_circles(storm_group, storm_data)
        
        # Add time-based markers
        if self.show_time_markers:
            self._add_time_markers(storm_group, storm_data)
        
        # Add start and end markers
        self._add_start_end_markers(storm_group, storm_data)
        
        # Add to map
        storm_group.add_to(folium_map)
        
        print(f"✓ Added storm layer with {len(storm_data)} data points")
        return storm_group
    
    def _extract_storm_data(self, tc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and process storm data from TC timeseries.
        
        Args:
            tc_data: Raw tropical cyclone data
            
        Returns:
            List of processed storm data points
        """
        storm_points = []
        
        if 'timeseries' not in tc_data:
            return storm_points
        
        for ts in tc_data['timeseries']:
            try:
                ts_data = ts['EventTimeseries']
                
                # Extract coordinates
                dimensions = ts_data.get('Dimensions', {})
                lat = dimensions.get('lat')
                lon = dimensions.get('lon')
                
                if lat is None or lon is None:
                    continue
                
                # Extract time
                header = ts_data.get('Header', {})
                time_str = header.get('time', '')
                
                # Extract surface data
                surface = ts_data.get('SurfaceNearSurface', {})
                
                # Calculate wind speed
                u_wind = surface.get('u10m', 0)
                v_wind = surface.get('v10m', 0)
                wind_speed = np.sqrt(u_wind**2 + v_wind**2)
                
                # Extract other parameters
                pressure = surface.get('msl', 0)
                precipitation = surface.get('tp', 0)
                
                # Extract cyclone parameters
                cyclone_params = ts_data.get('CycloneParameters', {})
                storm_size = cyclone_params.get('storm_size', 0)
                
                storm_point = {
                    'lat': float(lat),
                    'lon': float(lon),
                    'time': time_str,
                    'wind_speed': float(wind_speed),
                    'pressure': float(pressure / 100) if pressure else 0,  # Convert to hPa
                    'precipitation': float(precipitation * 1000) if precipitation else 0,  # Convert to mm
                    'storm_size': float(storm_size),
                    'u_wind': float(u_wind),
                    'v_wind': float(v_wind)
                }
                
                storm_points.append(storm_point)
                
            except Exception as e:
                print(f"Warning: Error processing storm data point: {e}")
                continue
        
        return storm_points
    
    def _add_storm_path(self, feature_group: folium.FeatureGroup, storm_data: List[Dict[str, Any]]):
        """
        Add the main storm track line to the feature group.
        
        Args:
            feature_group: Folium FeatureGroup to add the path to
            storm_data: Processed storm data points
        """
        if len(storm_data) < 2:
            return
        
        # Create coordinate list
        coordinates = [[point['lat'], point['lon']] for point in storm_data]
        
        # Create the storm path line
        storm_path = folium.PolyLine(
            coordinates,
            weight=4,
            color='#E63946',  # Bright red
            opacity=0.05,
            tooltip="Storm Track",
            popup=f"Storm Path ({len(coordinates)} points)"
        )
        
        storm_path.add_to(feature_group)
        
        print(f"✓ Added storm path with {len(coordinates)} coordinate points")
    
    def _add_storm_size_circles(self, feature_group: folium.FeatureGroup, storm_data: List[Dict[str, Any]]):
        """
        Add storm size circles to show the extent of the storm at each time point.
        
        Args:
            feature_group: Folium FeatureGroup to add circles to
            storm_data: Processed storm data points
        """
        for point in storm_data:
            if point['storm_size'] > 0:
                # Create circle for storm size
                storm_circle = folium.Circle(
                    location=[point['lat'], point['lon']],
                    radius=point['storm_size'] * 1000 / 2,  # Convert km to meters, radius not diameter
                    color='#E63946',
                    fill=True,
                    fillColor='#E63946',
                    fillOpacity=0.03,  # Very transparent
                    weight=0,  # No outline
                    popup=f"Storm extent: {point['storm_size']:.1f} km diameter"
                )
                
                storm_circle.add_to(feature_group)
        
        print(f"✓ Added {len([p for p in storm_data if p['storm_size'] > 0])} storm size circles")
    
    def _add_time_markers(self, feature_group: folium.FeatureGroup, storm_data: List[Dict[str, Any]]):
        """
        Add time-based markers along the storm path.
        
        Args:
            feature_group: Folium FeatureGroup to add markers to
            storm_data: Processed storm data points
        """
        # Calculate wind speed range for color mapping
        wind_speeds = [point['wind_speed'] for point in storm_data]
        min_speed = min(wind_speeds) if wind_speeds else 0
        max_speed = max(wind_speeds) if wind_speeds else 1
        
        marker_count = 0
        
        for i, point in enumerate(storm_data):
            # Add marker every nth data point
            if i % self.marker_interval == 0:
                try:
                    # Parse time
                    time_obj = datetime.strptime(point['time'], '%Y-%m-%dT%H:%M:%SZ')
                    
                    # Calculate marker color based on wind speed
                    if max_speed > min_speed:
                        norm_speed = (point['wind_speed'] - min_speed) / (max_speed - min_speed)
                    else:
                        norm_speed = 0.5
                    
                    # Generate color from blue (low) to red (high)
                    hue = (1 - norm_speed) * 0.7  # 0.7 is blue, 0 is red in HSV
                    rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
                    color = f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
                    
                    # Create detailed popup content
                    popup_content = self._create_marker_popup(point, time_obj)
                    
                    # Create marker
                    marker = folium.CircleMarker(
                        location=[point['lat'], point['lon']],
                        radius=6,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.8,
                        weight=2,
                        popup=folium.Popup(popup_content, max_width=300),
                        tooltip=f"Storm at {time_obj.strftime('%Y-%m-%d %H:%M')} | Wind: {point['wind_speed']:.1f} m/s"
                    )
                    
                    marker.add_to(feature_group)
                    marker_count += 1
                    
                except Exception as e:
                    print(f"Warning: Error creating time marker: {e}")
                    continue
        
        print(f"✓ Added {marker_count} time-based markers")
    
    def _add_start_end_markers(self, feature_group: folium.FeatureGroup, storm_data: List[Dict[str, Any]]):
        """
        Add distinctive start and end markers for the storm track.
        
        Args:
            feature_group: Folium FeatureGroup to add markers to
            storm_data: Processed storm data points
        """
        if not storm_data:
            return
        
        try:
            # Start marker
            start_point = storm_data[0]
            start_time = datetime.strptime(start_point['time'], '%Y-%m-%dT%H:%M:%SZ')
            
            start_marker = folium.Marker(
                location=[start_point['lat'], start_point['lon']],
                popup=f"<b>Storm Start</b><br>{start_time.strftime('%Y-%m-%d %H:%M')}<br>Wind: {start_point['wind_speed']:.1f} m/s",
                tooltip="Storm Start",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            )
            start_marker.add_to(feature_group)
            
            # End marker  
            end_point = storm_data[-1]
            end_time = datetime.strptime(end_point['time'], '%Y-%m-%dT%H:%M:%SZ')
            
            end_marker = folium.Marker(
                location=[end_point['lat'], end_point['lon']],
                popup=f"<b>Storm End</b><br>{end_time.strftime('%Y-%m-%d %H:%M')}<br>Wind: {end_point['wind_speed']:.1f} m/s",
                tooltip="Storm End",
                icon=folium.Icon(color='red', icon='stop', prefix='fa')
            )
            end_marker.add_to(feature_group)
            
            print("✓ Added start and end markers")
            
        except Exception as e:
            print(f"Warning: Error creating start/end markers: {e}")
    
    def _create_marker_popup(self, point: Dict[str, Any], time_obj: datetime) -> str:
        """
        Create detailed popup content for storm markers.
        
        Args:
            point: Storm data point
            time_obj: Parsed datetime object
            
        Returns:
            HTML string for popup content
        """
        popup_content = f"""
        <div style="font-family: Arial; width: 280px;">
            <h4 style="margin-bottom: 5px; color: #2874A6;">Storm Status</h4>
            <p style="margin-top: 0; color: #566573; font-size: 0.9em;">{time_obj.strftime('%Y-%m-%d %H:%M UTC')}</p>
            
            <div style="background-color: #EBF5FB; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #2874A6;">Location & Time</h5>
                <p style="margin: 2px 0;"><b>Coordinates:</b> {point['lat']:.4f}°N, {point['lon']:.4f}°E</p>
                <p style="margin: 2px 0;"><b>Time:</b> {time_obj.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div style="background-color: #FEF9E7; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #7D6608;">Wind & Pressure</h5>
                <p style="margin: 2px 0;"><b>Wind Speed:</b> {point['wind_speed']:.1f} m/s ({point['wind_speed']*2.237:.1f} mph)</p>
                <p style="margin: 2px 0;"><b>Pressure:</b> {point['pressure']:.1f} hPa</p>
                <p style="margin: 2px 0;"><b>Storm Size:</b> {point['storm_size']:.1f} km</p>
            </div>
            
            <div style="background-color: #E8F8F5; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #148F77;">Precipitation</h5>
                <p style="margin: 2px 0;"><b>Total Precipitation:</b> {point['precipitation']:.1f} mm</p>
            </div>
        </div>
        """
        
        return popup_content
    
    def configure(self, show_storm_size: bool = True, show_time_markers: bool = True,
                 marker_interval: int = 8, color_scheme: str = "wind_speed"):
        """
        Configure storm layer display options.
        
        Args:
            show_storm_size: Whether to show storm size circles
            show_time_markers: Whether to show time-based markers
            marker_interval: Interval for time markers (data points)
            color_scheme: Color scheme for markers ("wind_speed", "pressure", "time")
        """
        self.show_storm_size = show_storm_size
        self.show_time_markers = show_time_markers
        self.marker_interval = marker_interval
        self.color_scheme = color_scheme
        
        print(f"✓ Storm layer configured: size={show_storm_size}, markers={show_time_markers}, interval={marker_interval}")
    
    def get_storm_statistics(self, storm_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for the storm track.
        
        Args:
            storm_data: Processed storm data points
            
        Returns:
            Dictionary with storm statistics
        """
        if not storm_data:
            return {}
        
        wind_speeds = [point['wind_speed'] for point in storm_data]
        pressures = [point['pressure'] for point in storm_data if point['pressure'] > 0]
        storm_sizes = [point['storm_size'] for point in storm_data if point['storm_size'] > 0]
        
        return {
            'total_points': len(storm_data),
            'duration_hours': len(storm_data) * 0.5,  # Assuming 30-min intervals
            'max_wind_speed': max(wind_speeds) if wind_speeds else 0,
            'min_pressure': min(pressures) if pressures else 0,
            'avg_storm_size': np.mean(storm_sizes) if storm_sizes else 0,
            'track_length_km': self._calculate_track_length(storm_data)
        }
    
    def _calculate_track_length(self, storm_data: List[Dict[str, Any]]) -> float:
        """
        Calculate the total length of the storm track.
        
        Args:
            storm_data: Processed storm data points
            
        Returns:
            Track length in kilometers
        """
        if len(storm_data) < 2:
            return 0.0
        
        total_distance = 0.0
        
        for i in range(1, len(storm_data)):
            # Simple distance calculation (not accounting for Earth curvature)
            lat1, lon1 = storm_data[i-1]['lat'], storm_data[i-1]['lon']
            lat2, lon2 = storm_data[i]['lat'], storm_data[i]['lon']
            
            # Convert to approximate distance in km
            lat_diff = abs(lat2 - lat1) * 111  # 1 degree lat ≈ 111 km
            lon_diff = abs(lon2 - lon1) * 111 * np.cos(np.radians((lat1 + lat2) / 2))
            distance = np.sqrt(lat_diff**2 + lon_diff**2)
            
            total_distance += distance
        
        return total_distance