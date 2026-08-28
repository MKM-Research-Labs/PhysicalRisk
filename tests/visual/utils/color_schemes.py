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
        ("Very Low", "#2e7d32"),
        ("Very low", "#2e7d32"),
        ("Low", "#66bb6a"),
        ("Medium", "#ff9800"),
        ("High", "#f44336"),
        ("Very High", "#b71c1c"),
        ("Very high", "#b71c1c"),
        ("Unknown", "#2196f3"),
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
        assert ColorSchemes.get_ltv_risk_color(0.5) == "#27ae60"

    def test_medium_ltv_is_orange(self):
        assert ColorSchemes.get_ltv_risk_color(0.7) == "#f39c12"

    def test_high_ltv_is_red(self):
        assert ColorSchemes.get_ltv_risk_color(0.9) == "#e74c3c"

    def test_very_high_ltv_is_purple(self):
        assert ColorSchemes.get_ltv_risk_color(0.99) == "#8e44ad"

    def test_percentage_normalised(self):
        # 60% should be same as 0.60
        assert ColorSchemes.get_ltv_risk_color(60) == ColorSchemes.get_ltv_risk_color(0.60)


# ===========================================================================
# Flood depth color
# ===========================================================================

class TestDepthColor:

    def test_no_flood_is_light_green(self):
        assert ColorSchemes.get_depth_color(0.0) == "#e8f5e8"

    def test_negative_depth_is_no_flood(self):
        assert ColorSchemes.get_depth_color(-1.0) == "#e8f5e8"

    def test_minor_flooding(self):
        assert ColorSchemes.get_depth_color(0.3) == "#ffeb3b"

    def test_moderate_flooding(self):
        assert ColorSchemes.get_depth_color(0.8) == "#ff9800"

    def test_significant_flooding(self):
        assert ColorSchemes.get_depth_color(1.5) == "#f44336"

    def test_severe_flooding(self):
        assert ColorSchemes.get_depth_color(3.0) == "#9c27b0"


# ===========================================================================
# Folium color name
# ===========================================================================

class TestFoliumColorName:

    def test_known_colors_mapped(self):
        result = ColorSchemes.get_folium_color_name("#2e7d32")
        assert result == "green"

    def test_unknown_hex_returns_blue(self):
        result = ColorSchemes.get_folium_color_name("#aaaaaa")
        assert result == "blue"

    def test_red_mapped(self):
        result = ColorSchemes.get_folium_color_name("#f44336")
        assert result == "red"


# ===========================================================================
# Convenience functions
# ===========================================================================

class TestConvenienceFunctions:

    def test_get_risk_color_delegates(self):
        assert get_risk_color("High") == ColorSchemes.get_flood_risk_color("High")

    def test_get_status_color_delegates(self):
        assert get_status_color("Fully operational") == ColorSchemes.get_operational_status_color("Fully operational")


class TestResolvedFromConfig:
    """ColorSchemes holds no colour of its own — it resolves ``config.theme``.

    These are the tests that would fail if someone reintroduced a literal here, which
    is the failure mode rule R7 exists to prevent.
    """

    def test_ramps_match_the_config_tokens(self):
        from config.theme import FLOOD_RISK_TOKENS, THEME
        for level, token in FLOOD_RISK_TOKENS.items():
            assert ColorSchemes.FLOOD_RISK_COLORS[level] == THEME[token]

    def test_status_ramp_matches_the_config_tokens(self):
        from config.theme import OPERATIONAL_STATUS_TOKENS, THEME
        for status, token in OPERATIONAL_STATUS_TOKENS.items():
            assert ColorSchemes.OPERATIONAL_STATUS_COLORS[status] == THEME[token]

    def test_a_ramp_naming_an_undefined_token_fails_loudly(self):
        """Silence here would paint an element with None."""
        from visual.utils.color_schemes._core import _resolve
        with pytest.raises(KeyError, match="undefined design tokens"):
            _resolve({"Some band": "no-such-token"})

    def test_every_ramp_value_is_a_hex_colour(self):
        for ramp in (ColorSchemes.FLOOD_RISK_COLORS,
                     ColorSchemes.OPERATIONAL_STATUS_COLORS,
                     ColorSchemes.LOAN_RISK_COLORS,
                     ColorSchemes.PROPERTY_TYPE_COLORS,
                     ColorSchemes.STORM_INTENSITY_COLORS,
                     ColorSchemes.DEPTH_BAND_COLORS,
                     ColorSchemes.LTV_BAND_COLORS):
            for value, colour in ramp.items():
                assert colour.startswith("#") and len(colour) == 7, f"{value}: {colour}"


class TestBandBoundariesArePreserved:
    """The three numeric ramps disagree about which side of a bound a value sits on.

    Storm intensity bands on a strict ``<``, depth and LTV on ``<=``. That predates
    the theme package; these pin it so the inconsistency cannot be "tidied" into a
    silent recolouring of every marker sitting exactly on a boundary.
    """

    def test_storm_boundary_is_exclusive(self):
        assert ColorSchemes.get_wind_speed_color(30.0) == \
            ColorSchemes.STORM_INTENSITY_COLORS["moderate"]
        assert ColorSchemes.get_wind_speed_color(29.999) == \
            ColorSchemes.STORM_INTENSITY_COLORS["low"]
        assert ColorSchemes.get_wind_speed_color(70.0) == \
            ColorSchemes.STORM_INTENSITY_COLORS["extreme"]

    def test_depth_boundary_is_inclusive(self):
        assert ColorSchemes.get_depth_color(0.5) == \
            ColorSchemes.DEPTH_BAND_COLORS["minor"]
        assert ColorSchemes.get_depth_color(0.0) == \
            ColorSchemes.DEPTH_BAND_COLORS["none"]
        assert ColorSchemes.get_depth_color(2.0) == \
            ColorSchemes.DEPTH_BAND_COLORS["significant"]

    def test_ltv_boundary_is_inclusive(self):
        assert ColorSchemes.get_ltv_risk_color(0.6) == \
            ColorSchemes.LTV_BAND_COLORS["low"]
        assert ColorSchemes.get_ltv_risk_color(0.95) == \
            ColorSchemes.LTV_BAND_COLORS["high"]
        assert ColorSchemes.get_ltv_risk_color(0.951) == \
            ColorSchemes.LTV_BAND_COLORS["critical"]


class TestFloodRiskMarkers:
    """The Folium marker ramp, which three modules used to spell separately."""

    @pytest.mark.parametrize("level,expected", [
        ("Very Low", "green"), ("Very low", "green"), ("Low", "lightgreen"),
        ("Medium", "orange"), ("High", "red"), ("Very High", "darkred"),
        ("Very high", "darkred"), ("Unknown", "blue"), ("N/A", "gray"),
    ])
    def test_known_bands(self, level, expected):
        assert ColorSchemes.get_flood_risk_marker(level) == expected

    def test_unknown_band_falls_back_to_blue(self):
        assert ColorSchemes.get_flood_risk_marker("nonsense") == "blue"

    def test_the_three_former_copies_now_agree(self):
        """risk_assessors, popup_builder and ColorSchemes were three spellings."""
        from visual.popups.popup_builder import PopupBuilder
        from visual.utils.risk_assessors import get_risk_color

        builder = PopupBuilder()
        for level in ("Very Low", "Low", "Medium", "High", "Very High", "Unknown",
                      "N/A", "nonsense"):
            shared = ColorSchemes.get_flood_risk_marker(level)
            assert get_risk_color(level) == shared, level
            assert builder.get_risk_color(level) == shared, level

    def test_folium_name_lookup_accepts_either_hex_case(self):
        """The ramps were uppercase before they were tokens."""
        assert ColorSchemes.get_folium_color_name("#2E7D32") == "green"
        assert ColorSchemes.get_folium_color_name("#2e7d32") == "green"
