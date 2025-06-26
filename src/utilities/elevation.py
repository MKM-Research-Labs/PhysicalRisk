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
Distance-based elevation system for property portfolio analysis.

This module calculates property elevations based on distance from the nearest Thames point,
eliminating the need for external DEM files. Uses a slope model with random variation.

Replaces the previous DEM-based elevation system with a distance-based approach.
"""

import numpy as np
import math
import random
from typing import Tuple, Optional
from typing import List, Dict, Tuple

# Thames points with elevation data (lat, lon, elevation_meters)
THAMES_POINTS = [
    (51.4573, -0.3073, 11.13), (51.4600, -0.2950, 10.86),
    (51.4630, -0.2800, 10.44), (51.4660, -0.2650, 10.01),
    (51.4690, -0.2500, 9.91), (51.4720, -0.2350, 9.04),
    (51.4883, -0.2303, 8.01), (51.4750, -0.2214, 7.91),
    (51.46694, -0.21306, 7.81), (51.4700, -0.1980, 7.71),
    (51.4730, -0.1850, 7.61), (51.479134, -0.156838, 7.51),
    (51.4820, -0.1450, 7.41), (51.4850, -0.1350, 7.31),
    (51.4900, -0.1250, 7.21), (51.5005, -0.1198, 7.11),
    (51.5030, -0.1100, 7.01), (51.5052, -0.1168, 6.91),
    (51.5070, -0.1050, 6.81), (51.5097, -0.1044, 6.71),
    (51.5100, -0.0950, 6.61), (51.5079, -0.0878, 6.51),
    (51.505554, -0.075278, 6.41), (51.5030, -0.0650, 6.31),
    (51.5000, -0.0500, 6.21), (51.4970, -0.0350, 6.11),
    (51.4940, -0.0200, 6.01), (51.4910, -0.0050, 5.91),
    (51.4880, 0.0100, 5.81), (51.477928, -0.001545, 5.71),
    (51.4750, 0.0150, 5.61), (51.4720, 0.0300, 5.51),
    (51.4977, 0.0367, 5.41), (51.4765, 0.0539, 5.31),
    (51.4700, 0.0800, 5.21), (51.4650, 0.1200, 5.11),
    (51.4600, 0.1600, 5.01), (51.4550, 0.2000, 4.91),
    (51.4466, 0.2142, 4.81), (51.4400, 0.3000, 4.00)
]
# Extended area names along the Thames
LONDON_AREAS = [
    "Chelsea", "Kensington", "Westminster", "Camden", "Islington",
    "Hackney", "Tower Hamlets", "Southwark", "Lambeth", "Wandsworth",
    "Greenwich", "Lewisham", "Hammersmith", "Fulham", "Richmond",
    "Newham", "Barking", "Dagenham", "Havering", "Bexley",
    "Tilbury", "Thurrock", "Grays", "Purfleet", "Dartford",
    "Erith", "Belvedere", "Thamesmead", "Abbey Wood", "Woolwich"
]

LONDON_STREETS = {
    "Chelsea": ["Kings Road", "Cheyne Walk", "Royal Avenue", "Sloane Square", "Flood Street"],
    "Kensington": ["Kensington High Street", "Holland Park", "Pembroke Road", "Kensington Court"],
    "Westminster": ["Victoria Street", "Whitehall", "Birdcage Walk", "Great Smith Street"],
    "Camden": ["Camden High Street", "Parkway", "Chalk Farm Road", "Delancey Street"],
    "Islington": ["Upper Street", "Liverpool Road", "Essex Road", "Canonbury Square"],
    "Hackney": ["Mare Street", "Broadway Market", "Kingsland Road", "Dalston Lane"],
    "Tower Hamlets": ["Commercial Road", "Brick Lane", "Cable Street", "Roman Road"],
    "Southwark": ["Borough High Street", "Long Lane", "Tower Bridge Road", "Bermondsey Street"],
    "Lambeth": ["Kennington Road", "Lambeth Road", "Albert Embankment", "Camberwell New Road"],
    "Wandsworth": ["Wandsworth High Street", "East Hill", "Trinity Road", "Lavender Hill"]
}

# Property value factors by London area
AREA_VALUE_FACTORS = {
    'Chelsea': 2.0, 'Kensington': 1.9, 'Westminster': 1.8,
    'Camden': 1.5, 'Islington': 1.4, 'Hackney': 1.2,
    'Tower Hamlets': 1.3, 'Southwark': 1.2, 'Lambeth': 1.1,
    'Wandsworth': 1.4, 'Greenwich': 1.3, 'Lewisham': 1.1,
    'Hammersmith': 1.5, 'Fulham': 1.4, 'Richmond': 1.6,
    'Newham': 1.0, 'Barking': 0.9, 'Dagenham': 0.8,
    'Havering': 0.9, 'Bexley': 0.9, 'Tilbury': 0.7,
    'Thurrock': 0.8, 'Grays': 0.7, 'Purfleet': 0.8,
    'Dartford': 0.9, 'Erith': 0.8, 'Belvedere': 0.8,
    'Thamesmead': 0.9, 'Abbey Wood': 0.9, 'Woolwich': 1.0
}




class Elevation:
    """
    Calculate property elevations based on distance from Thames points.
    
    Uses a model that applies slope from Thames elevation plus random variation.
    """
    
    def __init__(self, max_slope_percent: float = 2.0, max_random_elevation: float = 10.0):
        """
        Initialize the elevation calculator.
        
        Args:
            max_slope_percent: Maximum slope percentage from Thames (default 2%)
            max_random_elevation: Maximum random elevation addition in meters (default 10m)
        """
        self.max_slope_percent = max_slope_percent
        self.max_random_elevation = max_random_elevation
        self.slope_factor = max_slope_percent / 100.0  # Convert percentage to decimal
    
    def _calculate_distance_meters(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates (decimal degrees)
            lat2, lon2: Second point coordinates (decimal degrees)
            
        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in meters
        earth_radius = 6371000
        
        return earth_radius * c
    
    def find_nearest_thames_point(self, lat: float, lon: float) -> Tuple[int, float, float]:
        """
        Find the nearest Thames point to given coordinates.
        
        Args:
            lat: Property latitude
            lon: Property longitude
            
        Returns:
            Tuple of (thames_point_index, distance_meters, thames_elevation)
        """
        min_distance = float('inf')
        nearest_idx = 0
        
        for i, thames_point in enumerate(THAMES_POINTS):
            thames_lat, thames_lon = thames_point[0], thames_point[1]
            distance = self._calculate_distance_meters(lat, lon, thames_lat, thames_lon)
            
            if distance < min_distance:
                min_distance = distance
                nearest_idx = i
        
        thames_elevation = THAMES_POINTS[nearest_idx][2]
        return nearest_idx, min_distance, thames_elevation
    
    def calculate_elevation(self, lat: float, lon: float, 
                          use_random: bool = True, 
                          random_seed: Optional[int] = None) -> dict:
        """
        Calculate elevation for a property at given coordinates.
        
        Args:
            lat: Property latitude
            lon: Property longitude
            use_random: Whether to add random elevation component
            random_seed: Optional seed for reproducible random values
            
        Returns:
            Dictionary with elevation details
        """
        if random_seed is not None:
            random.seed(random_seed)
        
        # Find nearest Thames point
        nearest_idx, distance_m, thames_elevation = self.find_nearest_thames_point(lat, lon)
        
        # Calculate slope-based elevation increase
        slope_elevation = distance_m * self.slope_factor
        
        # Calculate random elevation component with distance-based scaling
        if use_random:
            # No random component for distances < 50m
            if distance_m < 50.0:
                random_factor = 0.0
            # Gradually introduce random component from 50m to 250m
            elif distance_m < 250.0:
                random_factor = (distance_m - 50.0) / (250.0 - 50.0)  # Linear scale 0 to 1
            # Full random component for distances >= 250m
            else:
                random_factor = 1.0
            
            random_elevation = random.uniform(0, self.max_random_elevation * random_factor)
        else:
            random_elevation = 0.0
        
        # Total elevation
        total_elevation = thames_elevation + slope_elevation + random_elevation
        
        return {
            'total_elevation': round(total_elevation, 2),
            'thames_elevation': round(thames_elevation, 2),
            'slope_elevation': round(slope_elevation, 2),
            'random_elevation': round(random_elevation, 2),
            'distance_to_thames': round(distance_m, 1),
            'nearest_thames_idx': nearest_idx,
            'slope_percent': round((slope_elevation / distance_m * 100), 3) if distance_m > 0 else 0.0,
            'random_factor': round(random_factor if use_random else 0.0, 3)
        }
    
    def get_elevation(self, lat: float, lon: float) -> float:
        """
        Get elevation value for given coordinates.
        
        Args:
            lat: Property latitude
            lon: Property longitude
            
        Returns:
            Elevation in meters
        """
        result = self.calculate_elevation(lat, lon)
        return result['total_elevation']
    
    def get_elevation_direct_grid(self, lat: float, lon: float) -> float:
        """
        Get elevation using direct calculation (compatibility method).
        
        Args:
            lat: Property latitude
            lon: Property longitude
            
        Returns:
            Elevation in meters
        """
        return self.get_elevation(lat, lon)


# Standalone utility functions
def get_random_thames_point() -> Tuple[float, float, float]:
    """Get a random point along the Thames with elevation."""
    point = THAMES_POINTS[random.randint(0, len(THAMES_POINTS) - 1)]
    return point


def calculate_location_near_thames(distance_meters: float = None) -> Dict:
    """
    Generate a random location near the Thames.

    Args:
        distance_meters: Distance from the Thames in meters (100-1000)
                        If None, a random distance between 100-1000m is chosen

    Returns:
        Dictionary with location information including lat, lon, elevation, and nearest Thames point
    """
    thames_point_idx = random.randint(0, len(THAMES_POINTS) - 1)
    thames_point = THAMES_POINTS[thames_point_idx]

    if distance_meters is None:
        distance_meters = random.uniform(100, 1000)

    # Convert distance to degrees
    lat_deg_per_meter = 1 / 111000
    lon_deg_per_meter = 1 / (69400 * math.cos(math.radians(thames_point[0])))

    # Generate random angle
    angle_rad = math.radians(random.uniform(0, 360))

    # Calculate offset
    lat_offset = distance_meters * lat_deg_per_meter * math.cos(angle_rad)
    lon_offset = distance_meters * lon_deg_per_meter * math.sin(angle_rad)

    # Calculate new coordinates
    new_lat = thames_point[0] + lat_offset
    new_lon = thames_point[1] + lon_offset

    area_name = LONDON_AREAS[thames_point_idx % len(LONDON_AREAS)]

    return {
        "lat": new_lat,
        "lon": new_lon,
        "elevation": thames_point[2],  # Thames point elevation
        "name": area_name,
        "thames_point_idx": thames_point_idx,
        "distance_to_thames": distance_meters,
        "value_factor": 1.5 - (distance_meters / 2000)
    }


def generate_synchronized_locations(count: int) -> List[Dict]:
    """
    Generate a list of locations near the Thames with elevation data.

    Args:
        count: Number of locations to generate

    Returns:
        List of location dictionaries with elevation information
    """
    locations = []

    for i in range(min(count, len(THAMES_POINTS))):
        thames_point = THAMES_POINTS[i]
        distance_meters = random.uniform(100, 1000)

        lat_deg_per_meter = 1 / 111000
        lon_deg_per_meter = 1 / (69400 * math.cos(math.radians(thames_point[0])))

        angle_rad = math.radians(random.uniform(0, 360))

        lat_offset = distance_meters * lat_deg_per_meter * math.cos(angle_rad)
        lon_offset = distance_meters * lon_deg_per_meter * math.sin(angle_rad)

        new_lat = thames_point[0] + lat_offset
        new_lon = thames_point[1] + lon_offset

        area_name = LONDON_AREAS[i % len(LONDON_AREAS)]

        locations.append({
            "lat": new_lat,
            "lon": new_lon,
            "elevation": thames_point[2],  # Thames point elevation
            "name": area_name,
            "thames_point_idx": i,
            "distance_to_thames": distance_meters,
            "value_factor": AREA_VALUE_FACTORS.get(area_name, 1.0)
        })

    if count > len(THAMES_POINTS):
        for i in range(len(THAMES_POINTS), count):
            locations.append(calculate_location_near_thames())

    return locations


def get_thames_elevation_at_point(point_idx: int) -> float:
    """
    Get the elevation at a specific Thames point.
    
    Args:
        point_idx: Index of the Thames point (0-39)
        
    Returns:
        Elevation in meters
    """
    if 0 <= point_idx < len(THAMES_POINTS):
        return THAMES_POINTS[point_idx][2]
    else:
        raise IndexError(f"Thames point index {point_idx} out of range (0-{len(THAMES_POINTS)-1})")


def get_thames_point_info(point_idx: int) -> Dict:
    """
    Get complete information about a Thames point.
    
    Args:
        point_idx: Index of the Thames point (0-39)
        
    Returns:
        Dictionary with lat, lon, elevation, and area name
    """
    if 0 <= point_idx < len(THAMES_POINTS):
        point = THAMES_POINTS[point_idx]
        return {
            "lat": point[0],
            "lon": point[1],
            "elevation": point[2],
            "area_name": LONDON_AREAS[point_idx % len(LONDON_AREAS)],
            "point_idx": point_idx
        }
    else:
        raise IndexError(f"Thames point index {point_idx} out of range (0-{len(THAMES_POINTS)-1})")


# Global instance for easy access
_elevation_instance = None

def init_elevation_data(max_slope_percent: float = 2.0, 
                       max_random_elevation: float = 10.0) -> bool:
    """
    Initialize the global elevation calculator.
    
    Args:
        max_slope_percent: Maximum slope percentage from Thames (default 2%)
        max_random_elevation: Maximum random elevation addition in meters (default 10m)
        
    Returns:
        True if initialized successfully
    """
    global _elevation_instance
    
    try:
        _elevation_instance = Elevation(
            max_slope_percent=max_slope_percent,
            max_random_elevation=max_random_elevation
        )
        return True
    except Exception as e:
        print(f"Failed to initialize elevation calculator: {e}")
        return False

def get_elevation(lat: float, lon: float, method: str = 'interpolation') -> Optional[float]:
    """
    Get elevation for a specific latitude/longitude.
    
    Args:
        lat: Latitude value (WGS84)
        lon: Longitude value (WGS84)
        method: Method parameter for compatibility (ignored)
        
    Returns:
        Elevation in meters or None if unable to determine
    """
    global _elevation_instance
    
    if _elevation_instance is None:
        if not init_elevation_data():
            return None
    
    try:
        return _elevation_instance.get_elevation(lat, lon)
    except Exception as e:
        print(f"Error calculating elevation for ({lat}, {lon}): {e}")
        return None