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
Abstract base class for catchment implementations.

Each river catchment (Thames, Severn, Rhine, etc.) must implement this
interface to provide the geographic and configuration data needed for
portfolio generation.

Usage:
    from catchments.base_catchment import BaseCatchment
    
    class ThamesCatchment(BaseCatchment):
        @property
        def catchment_id(self) -> str:
            return "thames"
        # ... implement other abstract methods
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from config import config


class BaseCatchment(ABC):
    """
    Abstract base class defining the interface for catchment data.
    
    Each catchment implementation provides:
    - Geographic data (river points, bounds)
    - Location metadata (area names, streets)
    - Economic factors (property value multipliers)
    - Terrain generation capabilities
    """
    
    @property
    @abstractmethod
    def catchment_id(self) -> str:
        """
        Unique identifier for this catchment.
        
        Returns:
            Lowercase string identifier (e.g., 'thames', 'severn', 'rhine')
        """
        pass
    
    @property
    @abstractmethod
    def catchment_name(self) -> str:
        """
        Human-readable name for this catchment.
        
        Returns:
            Display name (e.g., 'River Thames', 'River Severn')
        """
        pass
    
    @property
    @abstractmethod
    def river_points(self) -> List[Tuple[float, float, float]]:
        """
        List of points along the river with elevations.
        
        Each point is a tuple of (latitude, longitude, elevation_meters).
        Points should be ordered from upstream to downstream.
        Used for gauge placement and flood modeling.
        
        Returns:
            List of (lat, lon, elevation) tuples
        """
        pass
    
    @property
    @abstractmethod
    def area_names(self) -> List[str]:
        """
        List of area/district names along the river.
        
        Used for property location generation and reporting.
        Should roughly correspond to river_points ordering.
        
        Returns:
            List of area/district names
        """
        pass
    
    @property
    @abstractmethod
    def bounds(self) -> Tuple[float, float, float, float]:
        """
        Geographic bounding box for this catchment.
        
        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        pass
    
    @property
    @abstractmethod
    def area_value_factors(self) -> Dict[str, float]:
        """
        Property value multipliers by area.
        
        Used to generate realistic property valuations based on
        location desirability. Factor of 1.0 is baseline.
        
        Returns:
            Dictionary mapping area names to value multipliers
        """
        pass
    
    @property
    def streets(self) -> Dict[str, List[str]]:
        """
        Street names by area for realistic address generation.
        
        Optional - returns empty dict if not implemented.
        
        Returns:
            Dictionary mapping area names to lists of street names
        """
        return {}
    
    @property
    def country(self) -> str:
        """
        Country code for this catchment.
        
        Returns:
            ISO country code (e.g., 'GB', 'DE', 'US')
        """
        return "GB"  # Default to UK
    
    @property
    def currency(self) -> str:
        """
        Currency code for property values in this catchment.
        
        Returns:
            ISO currency code (e.g., 'GBP', 'EUR', 'USD')
        """
        return "GBP"  # Default to British Pounds
    
    @property
    def flood_decision_bodies(self) -> List[str]:
        """
        Governmental bodies responsible for flood decisions.
        
        Used in gauge CDM for DecisionBody field.
        
        Returns:
            List of authority names
        """
        return ["Environment Agency"]  # Default UK body
    
    @property
    def gauge_owners(self) -> List[str]:
        """
        Organizations that own/operate flood gauges.
        
        Returns:
            List of organization names
        """
        return ["Environment Agency", "Local Authority"]
    
    @property
    def data_curators(self) -> List[str]:
        """
        Organizations that curate gauge data.
        
        Returns:
            List of organization names
        """
        return ["Environment Agency"]
    
    def get_terrain_generator(self) -> Optional[Any]:
        """
        Return the terrain DEM generator for this catchment.
        
        Override to provide catchment-specific terrain generation.
        
        Returns:
            Terrain generator class or None if not available
        """
        return None
    
    def get_elevation_at_point(self, lat: float, lon: float) -> float:
        """
        Get estimated elevation at a given coordinate.
        
        Default implementation interpolates from river_points.
        Override for more sophisticated elevation models.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Estimated elevation in meters
        """
        import math
        
        # Find nearest river point
        min_dist = float('inf')
        nearest_elevation = 10.0  # Default
        
        for rlat, rlon, relev in self.river_points:
            dist = math.sqrt((lat - rlat)**2 + (lon - rlon)**2)
            if dist < min_dist:
                min_dist = dist
                nearest_elevation = relev
        
        # Add some elevation for distance from river
        # Rough approximation: 1m rise per 100m distance
        distance_meters = min_dist * 111000  # Approximate degrees to meters
        elevation_rise = distance_meters * 0.01  # 1% slope
        
        return nearest_elevation + elevation_rise
    
    def get_area_for_point(self, lat: float, lon: float) -> str:
        """
        Get the area name for a given coordinate.
        
        Default implementation finds nearest river point and returns
        corresponding area.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Area name string
        """
        import math
        
        min_dist = float('inf')
        nearest_idx = 0
        
        for i, (rlat, rlon, _) in enumerate(self.river_points):
            dist = math.sqrt((lat - rlat)**2 + (lon - rlon)**2)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        # Map to area (cycling through if more points than areas)
        area_idx = nearest_idx % len(self.area_names)
        return self.area_names[area_idx]
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.catchment_id}')"
