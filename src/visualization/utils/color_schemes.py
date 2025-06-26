"""
Color scheme utilities for the visualization system.

This module provides consistent color mapping for different risk levels,
statuses, and data categories used throughout the visualization.
"""

import colorsys
from typing import Dict, List, Tuple, Union


class ColorSchemes:
    """Color scheme definitions and utilities for the visualization system."""
    
    # Risk level color mappings
    FLOOD_RISK_COLORS = {
        'Very Low': '#2E7D32',      # Dark green
        'Very low': '#2E7D32',      # Dark green (alternative casing)
        'Low': '#66BB6A',           # Light green
        'Medium': '#FF9800',        # Orange
        'High': '#F44336',          # Red
        'Very High': '#B71C1C',     # Dark red
        'Very high': '#B71C1C',     # Dark red (alternative casing)
        'Unknown': '#2196F3'        # Blue (default)
    }
    
    # Operational status colors for gauges
    OPERATIONAL_STATUS_COLORS = {
        'Fully operational': '#27AE60',      # Green
        'Maintenance required': '#F39C12',   # Orange
        'Temporarily offline': '#C0392B',    # Red
        'Decommissioned': '#7F8C8D',        # Gray
        'Unknown': '#3498DB'                 # Blue
    }
    
    # Mortgage risk colors
    MORTGAGE_RISK_COLORS = {
        'Low': '#27AE60',           # Green
        'Moderate': '#F39C12',      # Orange
        'High': '#E74C3C',          # Red
        'Critical': '#8E44AD',      # Purple
        'Unknown': '#34495E'        # Dark gray
    }
    
    # Property type colors
    PROPERTY_TYPE_COLORS = {
        'Residential': '#3498DB',    # Blue
        'Commercial': '#9B59B6',     # Purple
        'Industrial': '#E67E22',     # Orange
        'Mixed': '#1ABC9C',          # Teal
        'Unknown': '#95A5A6'         # Gray
    }
    
    # Storm intensity colors (based on wind speed)
    STORM_INTENSITY_COLORS = {
        'low': '#4CAF50',           # Green (< 30 m/s)
        'moderate': '#FF9800',      # Orange (30-50 m/s)
        'high': '#F44336',          # Red (50-70 m/s)
        'extreme': '#9C27B0'        # Purple (> 70 m/s)
    }
    
    @classmethod
    def get_flood_risk_color(cls, risk_level: str) -> str:
        """
        Get color for flood risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Hex color code
        """
        return cls.FLOOD_RISK_COLORS.get(risk_level, cls.FLOOD_RISK_COLORS['Unknown'])
    
    @classmethod
    def get_operational_status_color(cls, status: str) -> str:
        """
        Get color for operational status.
        
        Args:
            status: Operational status string
            
        Returns:
            Hex color code
        """
        return cls.OPERATIONAL_STATUS_COLORS.get(status, cls.OPERATIONAL_STATUS_COLORS['Unknown'])
    
    @classmethod
    def get_mortgage_risk_color(cls, risk_level: str) -> str:
        """
        Get color for mortgage risk level.
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Hex color code
        """
        return cls.MORTGAGE_RISK_COLORS.get(risk_level, cls.MORTGAGE_RISK_COLORS['Unknown'])
    
    @classmethod
    def get_property_type_color(cls, property_type: str) -> str:
        """
        Get color for property type.
        
        Args:
            property_type: Property type string
            
        Returns:
            Hex color code
        """
        return cls.PROPERTY_TYPE_COLORS.get(property_type, cls.PROPERTY_TYPE_COLORS['Unknown'])
    
    @classmethod
    def get_wind_speed_color(cls, wind_speed: float) -> str:
        """
        Get color based on wind speed.
        
        Args:
            wind_speed: Wind speed in m/s
            
        Returns:
            Hex color code
        """
        if wind_speed < 30:
            return cls.STORM_INTENSITY_COLORS['low']
        elif wind_speed < 50:
            return cls.STORM_INTENSITY_COLORS['moderate']
        elif wind_speed < 70:
            return cls.STORM_INTENSITY_COLORS['high']
        else:
            return cls.STORM_INTENSITY_COLORS['extreme']
    
    @classmethod
    def create_gradient_color(cls, value: float, min_value: float, max_value: float,
                            start_color: str = '#4CAF50', end_color: str = '#F44336') -> str:
        """
        Create a gradient color based on a value within a range.
        
        Args:
            value: Current value
            min_value: Minimum value in range
            max_value: Maximum value in range
            start_color: Color for minimum value (hex)
            end_color: Color for maximum value (hex)
            
        Returns:
            Interpolated hex color code
        """
        if max_value <= min_value:
            return start_color
        
        # Normalize value to 0-1 range
        normalized = max(0, min(1, (value - min_value) / (max_value - min_value)))
        
        # Convert hex to RGB
        start_rgb = cls._hex_to_rgb(start_color)
        end_rgb = cls._hex_to_rgb(end_color)
        
        # Interpolate RGB values
        interpolated_rgb = [
            int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * normalized)
            for i in range(3)
        ]
        
        # Convert back to hex
        return cls._rgb_to_hex(interpolated_rgb)
    
    @classmethod
    def create_hsv_gradient(cls, value: float, min_value: float, max_value: float,
                          start_hue: float = 0.3, end_hue: float = 0.0) -> str:
        """
        Create a gradient color using HSV color space.
        
        Args:
            value: Current value
            min_value: Minimum value in range
            max_value: Maximum value in range
            start_hue: Starting hue (0-1, where 0.3 is green, 0 is red)
            end_hue: Ending hue
            
        Returns:
            Hex color code
        """
        if max_value <= min_value:
            rgb = colorsys.hsv_to_rgb(start_hue, 0.8, 0.9)
        else:
            # Normalize value to 0-1 range
            normalized = max(0, min(1, (value - min_value) / (max_value - min_value)))
            
            # Interpolate hue
            hue = start_hue + (end_hue - start_hue) * normalized
            
            # Convert HSV to RGB
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        
        # Convert to hex
        return f'#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}'
    
    @classmethod
    def get_ltv_risk_color(cls, ltv_ratio: float) -> str:
        """
        Get color based on loan-to-value ratio.
        
        Args:
            ltv_ratio: LTV ratio (0-1 or 0-100)
            
        Returns:
            Hex color code
        """
        # Normalize to 0-1 if needed
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100
        
        if ltv_ratio <= 0.6:
            return '#27AE60'  # Green
        elif ltv_ratio <= 0.8:
            return '#F39C12'  # Orange
        elif ltv_ratio <= 0.95:
            return '#E74C3C'  # Red
        else:
            return '#8E44AD'  # Purple (very high risk)
    
    @classmethod
    def get_depth_color(cls, depth: float, max_depth: float = 5.0) -> str:
        """
        Get color based on flood depth.
        
        Args:
            depth: Flood depth in meters
            max_depth: Maximum depth for color scaling
            
        Returns:
            Hex color code
        """
        if depth <= 0:
            return '#E8F5E8'  # Very light green (no flood)
        elif depth <= 0.5:
            return '#FFEB3B'  # Yellow (minor flooding)
        elif depth <= 1.0:
            return '#FF9800'  # Orange (moderate flooding)
        elif depth <= 2.0:
            return '#F44336'  # Red (significant flooding)
        else:
            return '#9C27B0'  # Purple (severe flooding)
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def _rgb_to_hex(rgb: List[int]) -> str:
        """Convert RGB list to hex color."""
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    
    @classmethod
    def get_folium_color_name(cls, hex_color: str) -> str:
        """
        Convert hex color to closest Folium color name.
        
        Args:
            hex_color: Hex color code
            
        Returns:
            Folium-compatible color name
        """
        # Map of common hex colors to Folium color names
        color_map = {
            '#2E7D32': 'green',
            '#66BB6A': 'lightgreen',
            '#FF9800': 'orange',
            '#F44336': 'red',
            '#B71C1C': 'darkred',
            '#2196F3': 'blue',
            '#27AE60': 'green',
            '#F39C12': 'orange',
            '#C0392B': 'red',
            '#7F8C8D': 'gray',
            '#3498DB': 'blue',
            '#E74C3C': 'red',
            '#8E44AD': 'purple',
            '#34495E': 'darkblue'
        }
        
        return color_map.get(hex_color, 'blue')


# Convenience functions for backward compatibility
def get_risk_color(risk_level: str) -> str:
    """Get color for risk level (backward compatibility)."""
    return ColorSchemes.get_flood_risk_color(risk_level)

def get_status_color(status: str) -> str:
    """Get color for status (backward compatibility)."""
    return ColorSchemes.get_operational_status_color(status)