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
Tests for visual.utils.color_schemes.

Covers: ColorSchemes class methods (flood risk, operational status, mortgage
risk, property type, wind speed, gradient, HSV gradient, LTV, flood depth,
Folium mapping), and convenience functions.
"""

import pytest

from visual.utils.color_schemes import ColorSchemes, get_risk_color, get_status_color


# ===========================================================================
# Flood risk colors
# ===========================================================================

class TestFloodRiskColor:

    @pytest.mark.parametrize("level,expected", [
        ("Very Low", "#2E7D32"),
        ("Very low", "#2E7D32"),
        ("Low", "#66BB6A"),
        ("Medium", "#FF9800"),
        ("High", "#F44336"),
        ("Very High", "#B71C1C"),
        ("Very high", "#B71C1C"),
        ("Unknown", "#2196F3"),
    ])
    def test_known_levels(self, level, expected):
        assert ColorSchemes.get_flood_risk_color(level) == expected

    def test_unknown_level_returns_default(self):
        result = ColorSchemes.get_flood_risk_color("NotARiskLevel")
        assert result == ColorSchemes.FLOOD_RISK_COLORS["Unknown"]

    def test_returns_string(self):
        assert isinstance(ColorSchemes.get_flood_risk_color("High"), str)


# ===========================================================================
# Operational status colors
# ===========================================================================

class TestOperationalStatusColor:

    @pytest.mark.parametrize("status", [
        "Fully operational", "Maintenance required",
        "Temporarily offline", "Decommissioned",
    ])
    def test_known_statuses(self, status):
        result = ColorSchemes.get_operational_status_color(status)
        assert isinstance(result, str)
        assert result.startswith("#")

    def test_unknown_status_returns_default(self):
        result = ColorSchemes.get_operational_status_color("Broken")
        assert result == ColorSchemes.OPERATIONAL_STATUS_COLORS["Unknown"]


# ===========================================================================
# Loan risk colors
# ===========================================================================

class TestLoanRiskColor:

    @pytest.mark.parametrize("level", ["Low", "Moderate", "High", "Critical"])
    def test_known_levels(self, level):
        result = ColorSchemes.get_loan_risk_color(level)
        assert isinstance(result, str)
        assert result.startswith("#")

    def test_unknown_returns_default(self):
        result = ColorSchemes.get_loan_risk_color("Extreme")
        assert result == ColorSchemes.LOAN_RISK_COLORS["Unknown"]


# ===========================================================================
# Property type colors
# ===========================================================================

class TestPropertyTypeColor:

    @pytest.mark.parametrize("ptype", ["Residential", "Commercial", "Industrial", "Mixed"])
    def test_known_types(self, ptype):
        result = ColorSchemes.get_property_type_color(ptype)
        assert isinstance(result, str)

    def test_unknown_type_returns_default(self):
        result = ColorSchemes.get_property_type_color("Agricultural")
        assert result == ColorSchemes.PROPERTY_TYPE_COLORS["Unknown"]


# ===========================================================================
# Wind speed color
# ===========================================================================

class TestWindSpeedColor:

    def test_low_speed(self):
        result = ColorSchemes.get_wind_speed_color(20.0)
        assert result == ColorSchemes.STORM_INTENSITY_COLORS["low"]

    def test_moderate_speed(self):
        result = ColorSchemes.get_wind_speed_color(40.0)
        assert result == ColorSchemes.STORM_INTENSITY_COLORS["moderate"]

    def test_high_speed(self):
        result = ColorSchemes.get_wind_speed_color(60.0)
        assert result == ColorSchemes.STORM_INTENSITY_COLORS["high"]

    def test_extreme_speed(self):
        result = ColorSchemes.get_wind_speed_color(80.0)
        assert result == ColorSchemes.STORM_INTENSITY_COLORS["extreme"]

    def test_boundary_30(self):
        # 30 is NOT < 30, so goes to "moderate"
        result = ColorSchemes.get_wind_speed_color(30.0)
        assert result == ColorSchemes.STORM_INTENSITY_COLORS["moderate"]


# ===========================================================================
# Gradient colors
# ===========================================================================

class TestCreateGradientColor:

    def test_returns_hex_string(self):
        result = ColorSchemes.create_gradient_color(0.5, 0, 1)
        assert result.startswith("#")
        assert len(result) == 7

    def test_at_min_returns_start_color(self):
        result = ColorSchemes.create_gradient_color(0, 0, 1, "#000000", "#ffffff")
        assert result == "#000000"

    def test_at_max_returns_end_color(self):
        result = ColorSchemes.create_gradient_color(1, 0, 1, "#000000", "#ffffff")
        assert result == "#ffffff"

    def test_equal_min_max_returns_start_color(self):
        result = ColorSchemes.create_gradient_color(5, 5, 5, "#abcdef", "#123456")
        assert result == "#abcdef"

    def test_midpoint_is_between(self):
        # At midpoint between #000000 and #ffffff we expect #7f7f7f or similar
        result = ColorSchemes.create_gradient_color(0.5, 0, 1, "#000000", "#ffffff")
        r_val = int(result[1:3], 16)
        assert 100 < r_val < 160


class TestCreateHSVGradient:

    def test_returns_hex_string(self):
        result = ColorSchemes.create_hsv_gradient(0.5, 0, 1)
        assert result.startswith("#")
        assert len(result) == 7

    def test_equal_min_max_returns_start_hue_color(self):
        result = ColorSchemes.create_hsv_gradient(5, 5, 5, start_hue=0.3)
        assert result.startswith("#")

    def test_different_values_give_different_colors(self):
        r1 = ColorSchemes.create_hsv_gradient(0.0, 0, 1)
        r2 = ColorSchemes.create_hsv_gradient(1.0, 0, 1)
        assert r1 != r2


# ===========================================================================
# LTV risk color
# ===========================================================================

class TestLTVRiskColor:

    def test_low_ltv_is_green(self):
        assert ColorSchemes.get_ltv_risk_color(0.5) == "#27AE60"

    def test_medium_ltv_is_orange(self):
        assert ColorSchemes.get_ltv_risk_color(0.7) == "#F39C12"

    def test_high_ltv_is_red(self):
        assert ColorSchemes.get_ltv_risk_color(0.9) == "#E74C3C"

    def test_very_high_ltv_is_purple(self):
        assert ColorSchemes.get_ltv_risk_color(0.99) == "#8E44AD"

    def test_percentage_normalised(self):
        # 60% should be same as 0.60
        assert ColorSchemes.get_ltv_risk_color(60) == ColorSchemes.get_ltv_risk_color(0.60)


# ===========================================================================
# Flood depth color
# ===========================================================================

class TestDepthColor:

    def test_no_flood_is_light_green(self):
        assert ColorSchemes.get_depth_color(0.0) == "#E8F5E8"

    def test_negative_depth_is_no_flood(self):
        assert ColorSchemes.get_depth_color(-1.0) == "#E8F5E8"

    def test_minor_flooding(self):
        assert ColorSchemes.get_depth_color(0.3) == "#FFEB3B"

    def test_moderate_flooding(self):
        assert ColorSchemes.get_depth_color(0.8) == "#FF9800"

    def test_significant_flooding(self):
        assert ColorSchemes.get_depth_color(1.5) == "#F44336"

    def test_severe_flooding(self):
        assert ColorSchemes.get_depth_color(3.0) == "#9C27B0"


# ===========================================================================
# Folium color name
# ===========================================================================

class TestFoliumColorName:

    def test_known_colors_mapped(self):
        result = ColorSchemes.get_folium_color_name("#2E7D32")
        assert result == "green"

    def test_unknown_hex_returns_blue(self):
        result = ColorSchemes.get_folium_color_name("#AAAAAA")
        assert result == "blue"

    def test_red_mapped(self):
        result = ColorSchemes.get_folium_color_name("#F44336")
        assert result == "red"


# ===========================================================================
# Convenience functions
# ===========================================================================

class TestConvenienceFunctions:

    def test_get_risk_color_delegates(self):
        assert get_risk_color("High") == ColorSchemes.get_flood_risk_color("High")

    def test_get_status_color_delegates(self):
        assert get_status_color("Fully operational") == ColorSchemes.get_operational_status_color("Fully operational")
