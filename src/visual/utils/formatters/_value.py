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

"""Value formatters — floats, currency, percentage, coordinates, date, address."""

from datetime import datetime
from typing import Any


class _ValueFormattersMixin:
    """Scalar/text value formatting helpers."""

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
