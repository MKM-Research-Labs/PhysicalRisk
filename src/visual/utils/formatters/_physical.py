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

"""Physical-quantity formatters — age, distance, wind, pressure, precipitation."""

from datetime import datetime
from typing import Union


class _PhysicalFormattersMixin:
    """Physical-unit formatting helpers."""

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
