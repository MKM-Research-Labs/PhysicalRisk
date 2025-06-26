"""
Data formatting utilities for the visualization system.

This module provides consistent formatting functions for various data types
including currency, dates, coordinates, and safe number formatting.
"""

from datetime import datetime
from typing import Union, Optional, Any


class DataFormatter:
    """Utility class for consistent data formatting across the visualization system."""
    
    @staticmethod
    def safe_format_float(value: Any, decimals: int = 2) -> str:
        """
        Safely format a value as float with specified decimal places.
        
        Args:
            value: The value to format (can be None, string, int, float)
            decimals: Number of decimal places
            
        Returns:
            Formatted string or "N/A" if value cannot be formatted
        """
        if value in [None, "N/A", ""]:
            return "N/A"
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value) if value is not None else "N/A"
    
    @staticmethod
    def format_currency(value: Any, currency_symbol: str = "£") -> str:
        """
        Format a value as currency with proper comma separation.
        
        Args:
            value: The value to format
            currency_symbol: Currency symbol to use
            
        Returns:
            Formatted currency string or "N/A" if value cannot be formatted
        """
        if value in [None, "N/A", ""]:
            return "N/A"
        
        try:
            if isinstance(value, (int, float)):
                return f"{currency_symbol}{value:,.2f}"
            else:
                # Try to convert to float and format
                return f"{currency_symbol}{float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value) if value is not None else "N/A"
    
    @staticmethod
    def format_percentage(value: Any, decimals: int = 1) -> str:
        """
        Format a value as percentage.
        
        Args:
            value: The value to format (should be 0-1 for decimal, or 0-100 for percentage)
            decimals: Number of decimal places
            
        Returns:
            Formatted percentage string
        """
        if value in [None, "N/A", ""]:
            return "N/A"
        
        try:
            num_value = float(value)
            # If value is between 0 and 1, assume it's a decimal
            if 0 <= num_value <= 1:
                return f"{num_value * 100:.{decimals}f}%"
            # Otherwise assume it's already a percentage
            else:
                return f"{num_value:.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value) if value is not None else "N/A"
    
    @staticmethod
    def format_coordinates(lat: float, lon: float, decimals: int = 4) -> str:
        """
        Format latitude and longitude coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            decimals: Number of decimal places
            
        Returns:
            Formatted coordinate string
        """
        if lat is None or lon is None:
            return "N/A"
        
        try:
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"
            return f"{abs(lat):.{decimals}f}°{lat_dir}, {abs(lon):.{decimals}f}°{lon_dir}"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_date(date_str: str, input_format: str = '%Y-%m-%dT%H:%M:%SZ', 
                   output_format: str = '%Y-%m-%d %H:%M') -> str:
        """
        Format a date string from one format to another.
        
        Args:
            date_str: Input date string
            input_format: Format of the input string
            output_format: Desired output format
            
        Returns:
            Formatted date string or original string if parsing fails
        """
        if not date_str or date_str == "Unknown":
            return "Unknown"
        
        try:
            date_obj = datetime.strptime(date_str, input_format)
            return date_obj.strftime(output_format)
        except (ValueError, TypeError):
            return str(date_str)
    
    @staticmethod
    def format_address(address_dict: dict) -> str:
        """
        Format an address dictionary into a readable string.
        
        Args:
            address_dict: Dictionary containing address components
            
        Returns:
            Formatted address string
        """
        if not address_dict:
            return "N/A"
        
        parts = []
        
        # Building number and street name
        building_number = address_dict.get('building_number', '').strip()
        street_name = address_dict.get('street_name', '').strip()
        
        if building_number and street_name:
            parts.append(f"{building_number} {street_name}")
        elif street_name:
            parts.append(street_name)
        
        # Town/City
        town_city = address_dict.get('town_city', '').strip()
        if town_city:
            parts.append(town_city)
        
        # Postcode
        post_code = address_dict.get('post_code', '').strip()
        if post_code:
            parts.append(post_code)
        
        return ', '.join(parts) if parts else "N/A"
    
    @staticmethod
    def format_property_age(construction_year: Union[int, str]) -> str:
        """
        Calculate and format property age category.
        
        Args:
            construction_year: Year the property was constructed
            
        Returns:
            Age category string
        """
        if not construction_year or construction_year == 'Unknown':
            return "Unknown"
        
        try:
            year = int(construction_year)
            current_year = datetime.now().year
            age = current_year - year
            
            if age > 100:
                return f"High Risk (Pre-{current_year - 100})"
            elif age > 50:
                return f"Medium Risk ({current_year - 100}-{current_year - 50})"
            else:
                return f"Low Risk (Post-{current_year - 50})"
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_distance(distance_km: float, unit: str = "km") -> str:
        """
        Format distance with appropriate units.
        
        Args:
            distance_km: Distance in kilometers
            unit: Preferred unit ("km" or "m")
            
        Returns:
            Formatted distance string
        """
        if distance_km is None:
            return "N/A"
        
        try:
            if unit == "m" or distance_km < 1:
                return f"{distance_km * 1000:.0f} m"
            else:
                return f"{distance_km:.2f} km"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_wind_speed(u_component: float, v_component: float, 
                         unit: str = "m/s") -> str:
        """
        Calculate and format wind speed from u and v components.
        
        Args:
            u_component: U (eastward) wind component
            v_component: V (northward) wind component
            unit: Output unit ("m/s" or "mph")
            
        Returns:
            Formatted wind speed string
        """
        try:
            speed_ms = (u_component**2 + v_component**2)**0.5
            
            if unit == "mph":
                speed = speed_ms * 2.237  # Convert m/s to mph
                return f"{speed:.1f} mph"
            else:
                return f"{speed_ms:.1f} m/s"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_pressure(pressure_pa: float, unit: str = "hPa") -> str:
        """
        Format atmospheric pressure.
        
        Args:
            pressure_pa: Pressure in Pascals
            unit: Output unit ("hPa" or "mb")
            
        Returns:
            Formatted pressure string
        """
        try:
            if unit in ["hPa", "mb"]:
                pressure_hpa = pressure_pa / 100
                return f"{pressure_hpa:.1f} {unit}"
            else:
                return f"{pressure_pa:.0f} Pa"
        except (ValueError, TypeError):
            return "N/A"
    
    @staticmethod
    def format_precipitation(precip_m: float, unit: str = "mm") -> str:
        """
        Format precipitation amount.
        
        Args:
            precip_m: Precipitation in meters
            unit: Output unit ("mm" or "in")
            
        Returns:
            Formatted precipitation string
        """
        try:
            if unit == "in":
                precip_in = precip_m * 39.3701  # Convert m to inches
                return f"{precip_in:.2f} in"
            else:
                precip_mm = precip_m * 1000  # Convert m to mm
                return f"{precip_mm:.1f} mm"
        except (ValueError, TypeError):
            return "N/A"


# Convenience functions for backward compatibility
safe_format_float = DataFormatter.safe_format_float
format_currency = DataFormatter.format_currency
format_percentage = DataFormatter.format_percentage
format_coordinates = DataFormatter.format_coordinates
format_date = DataFormatter.format_date
format_address = DataFormatter.format_address