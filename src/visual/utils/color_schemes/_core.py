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

"""
Color scheme utilities for the visualization system.

Provides consistent color mapping for different risk levels, statuses, and
data categories. Gradient generation lives in the _gradient mixin.
"""

from ._gradient import _GradientMixin


class ColorSchemes(_GradientMixin):
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

    # Loan risk colors
    LOAN_RISK_COLORS = {
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
    def get_loan_risk_color(cls, risk_level: str) -> str:
        """
        Get color for loan risk level.

        Args:
            risk_level: Risk level string

        Returns:
            Hex color code
        """
        return cls.LOAN_RISK_COLORS.get(risk_level, cls.LOAN_RISK_COLORS['Unknown'])

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
