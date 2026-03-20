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

"""
Base catchment module defining the abstract interface for river catchments.

All catchment implementations must inherit from BaseCatchment and provide
the required attributes and methods for elevation calculation, gauge point
lookup, and area definitions.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
import math
import random


class BaseCatchment(ABC):
    """
    Abstract base class for river catchment definitions.
    
    Each catchment represents a river system with associated gauge points,
    elevation data, and geographic area definitions. Catchments have a 1:1
    relationship with portfolios, gauges, storm timeseries, and maps.
    
    Subclasses must define:
        - NAME: Unique identifier (e.g., 'thames')
        - REGION: Geographic region ('Europe' or 'NorthAmerica')
        - DISPLAYNAME: Human-readable name (e.g., 'Thames')
        - COUNTRY: Primary country/countries
        - GAUGEPOINTS: List of (lat, lon, elevation) tuples
        - AREAS: List of area names along the river
        - AREAVALUEFACTORS: Property value multipliers by area
    """
    
    # Required class attributes - must be overridden by subclasses
    NAME: str = ""
    REGION: str = ""
    DISPLAYNAME: str = ""
    COUNTRY: str = ""
    
    # Gauge points: List of (lat, lon, elevation_meters)
    GAUGEPOINTS: List[Tuple[float, float, float]] = []
    
    # Area definitions
    AREAS: List[str] = []
    STREETS: Dict[str, List[str]] = {}
    AREAVALUEFACTORS: Dict[str, float] = {}
    
    # Elevation model parameters (can be overridden)
    MAXSLOPEPERCENT: float = 2.0
    MAXRANDOMELEVATION: float = 10.0
    
    def __init__(self):
        """Initialize the catchment with elevation calculation parameters."""
        self.slopefactor = self.MAXSLOPEPERCENT / 100.0
    
    def get_elevation(self, lat: float, lon: float, 
                     userandom: bool = True,
                     randomseed: Optional[int] = None) -> float:
        """
        Get elevation at coordinates.
        
        Args:
            lat: Latitude (decimal degrees)
            lon: Longitude (decimal degrees)
            userandom: Whether to add random elevation component
            randomseed: Optional seed for reproducible values
            
        Returns:
            Elevation in meters
        """
        result = self.calculate_elevation(lat, lon, userandom, randomseed)
        return result['totalelevation']
    
    def find_nearest_gauge(self, lat: float, lon: float) -> Tuple[int, float, float]:
        """
        Find nearest gauge point to given coordinates.
        
        Args:
            lat: Latitude (decimal degrees)
            lon: Longitude (decimal degrees)
            
        Returns:
            Tuple of (gauge_index, distance_meters, gauge_elevation)
        """
        mindistance = float('inf')
        nearestidx = 0
        
        for i, gaugepoint in enumerate(self.GAUGEPOINTS):
            gaugelat, gaugelon = gaugepoint[0], gaugepoint[1]
            distance = self._calculate_distance_meters(lat, lon, gaugelat, gaugelon)
            
            if distance < mindistance:
                mindistance = distance
                nearestidx = i
        
        gaugeelevation = self.GAUGEPOINTS[nearestidx][2] if self.GAUGEPOINTS else 0.0
        return nearestidx, mindistance, gaugeelevation
    
    def calculate_elevation(self, lat: float, lon: float,
                           userandom: bool = True,
                           randomseed: Optional[int] = None) -> Dict:
        """
        Calculate detailed elevation for coordinates.
        
        Uses a model that applies slope from gauge elevation plus random variation.
        
        Args:
            lat: Latitude (decimal degrees)
            lon: Longitude (decimal degrees)
            userandom: Whether to add random elevation component
            randomseed: Optional seed for reproducible values
            
        Returns:
            Dictionary with elevation details
        """
        if randomseed is not None:
            random.seed(randomseed)
        
        if not self.GAUGEPOINTS:
            return {
                'totalelevation': 0.0,
                'gaugeelevation': 0.0,
                'slopeelevation': 0.0,
                'randomelevation': 0.0,
                'distancetogauge': 0.0,
                'nearestgaugeidx': 0,
                'slopepercent': 0.0,
                'randomfactor': 0.0
            }
        
        # Find nearest gauge point
        nearestidx, distancem, gaugeelevation = self.find_nearest_gauge(lat, lon)
        
        # Calculate slope-based elevation increase
        slopeelevation = distancem * self.slopefactor
        
        # Calculate random elevation component with distance-based scaling
        if userandom:
            if distancem < 50.0:
                randomfactor = 0.0
            elif distancem < 250.0:
                randomfactor = (distancem - 50.0) / (250.0 - 50.0)
            else:
                randomfactor = 1.0
            
            randomelevation = random.uniform(0, self.MAXRANDOMELEVATION * randomfactor)
        else:
            randomfactor = 0.0
            randomelevation = 0.0
        
        # Total elevation
        totalelevation = gaugeelevation + slopeelevation + randomelevation
        
        return {
            'totalelevation': round(totalelevation, 2),
            'gaugeelevation': round(gaugeelevation, 2),
            'slopeelevation': round(slopeelevation, 2),
            'randomelevation': round(randomelevation, 2),
            'distancetogauge': round(distancem, 1),
            'nearestgaugeidx': nearestidx,
            'slopepercent': round((slopeelevation / distancem * 100), 3) if distancem > 0 else 0.0,
            'randomfactor': round(randomfactor, 3)
        }
    
    def _calculate_distance_meters(self, lat1: float, lon1: float, 
                                   lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates (decimal degrees)
            lat2, lon2: Second point coordinates (decimal degrees)
            
        Returns:
            Distance in meters
        """
        lat1rad = math.radians(lat1)
        lon1rad = math.radians(lon1)
        lat2rad = math.radians(lat2)
        lon2rad = math.radians(lon2)
        
        dlat = lat2rad - lat1rad
        dlon = lon2rad - lon1rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1rad) * math.cos(lat2rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        earthradius = 6371000  # meters
        
        return earthradius * c
    
    @classmethod
    def get_bounds(cls) -> Tuple[float, float, float, float]:
        """
        Get bounding box for the catchment gauge points.
        
        Returns:
            Tuple of (min_lat, min_lon, max_lat, max_lon)
        """
        if not cls.GAUGEPOINTS:
            return (0.0, 0.0, 0.0, 0.0)
        
        lats = [p[0] for p in cls.GAUGEPOINTS]
        lons = [p[1] for p in cls.GAUGEPOINTS]
        return (min(lats), min(lons), max(lats), max(lons))
    
    @classmethod
    def get_center(cls) -> Tuple[float, float]:
        """
        Get center point of the catchment.
        
        Returns:
            Tuple of (center_lat, center_lon)
        """
        if not cls.GAUGEPOINTS:
            return (0.0, 0.0)
        
        lats = [p[0] for p in cls.GAUGEPOINTS]
        lons = [p[1] for p in cls.GAUGEPOINTS]
        return (sum(lats) / len(lats), sum(lons) / len(lons))
    
    @classmethod
    def get_gauge_count(cls) -> int:
        """Get number of gauge points."""
        return len(cls.GAUGEPOINTS)
    
    @classmethod
    def get_area_value_factor(cls, areaname: str) -> float:
        """
        Get property value factor for an area.
        
        Args:
            areaname: Name of the area
            
        Returns:
            Value factor (default 1.0 if area not found)
        """
        return cls.AREAVALUEFACTORS.get(areaname, 1.0)
    
    def get_gauge_info(self, pointidx: int) -> Dict:
        """
        Get complete information about a gauge point.
        
        Args:
            pointidx: Index of the gauge point
            
        Returns:
            Dictionary with lat, lon, elevation, and area name
        """
        if not self.GAUGEPOINTS or pointidx < 0 or pointidx >= len(self.GAUGEPOINTS):
            raise IndexError(f"Gauge point index {pointidx} out of range")
        
        point = self.GAUGEPOINTS[pointidx]
        areaname = self.AREAS[pointidx % len(self.AREAS)] if self.AREAS else "Unknown"
        
        return {
            "lat": point[0],
            "lon": point[1],
            "elevation": point[2],
            "areaname": areaname,
            "pointidx": pointidx
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.NAME}', gauges={self.get_gauge_count()})"
