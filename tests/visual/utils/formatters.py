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
Tests for visual.utils.formatters — DataFormatter class.

Covers all static methods: safe_format_float, format_currency,
format_percentage, format_coordinates, format_date, format_address,
format_property_age, format_distance, format_wind_speed, format_pressure,
format_precipitation, and backward-compat convenience aliases.
"""

import pytest

from visual.utils.formatters import DataFormatter


# ===========================================================================
# safe_format_float
# ===========================================================================

class TestSafeFormatFloat:

    def test_none_returns_na(self):
        assert DataFormatter.safe_format_float(None) == "N/A"

    def test_empty_string_returns_na(self):
        assert DataFormatter.safe_format_float("") == "N/A"

    def test_na_string_returns_na(self):
        assert DataFormatter.safe_format_float("N/A") == "N/A"

    def test_int_formatted(self):
        assert DataFormatter.safe_format_float(3) == "3.00"

    def test_float_formatted(self):
        assert DataFormatter.safe_format_float(3.14159) == "3.14"

    def test_custom_decimals(self):
        assert DataFormatter.safe_format_float(3.14159, decimals=4) == "3.1416"

    def test_string_number_converted(self):
        assert DataFormatter.safe_format_float("2.5") == "2.50"

    def test_non_numeric_string_returned_as_is(self):
        result = DataFormatter.safe_format_float("abc")
        assert result == "abc"


# ===========================================================================
# format_currency
# ===========================================================================

class TestFormatCurrency:

    def test_none_returns_na(self):
        assert DataFormatter.format_currency(None) == "N/A"

    def test_empty_returns_na(self):
        assert DataFormatter.format_currency("") == "N/A"

    def test_integer_formatted(self):
        assert DataFormatter.format_currency(1000) == "£1,000.00"

    def test_large_number_with_commas(self):
        assert DataFormatter.format_currency(1_000_000) == "£1,000,000.00"

    def test_custom_symbol(self):
        result = DataFormatter.format_currency(500, currency_symbol="$")
        assert result.startswith("$")

    def test_string_number_converted(self):
        result = DataFormatter.format_currency("250000")
        assert "250,000.00" in result

    def test_non_numeric_returned_as_is(self):
        result = DataFormatter.format_currency("NOT_A_NUMBER")
        assert result == "NOT_A_NUMBER"


# ===========================================================================
# format_percentage
# ===========================================================================

class TestFormatPercentage:

    def test_none_returns_na(self):
        assert DataFormatter.format_percentage(None) == "N/A"

    def test_empty_returns_na(self):
        assert DataFormatter.format_percentage("") == "N/A"

    def test_decimal_fraction_multiplied(self):
        result = DataFormatter.format_percentage(0.25)
        assert result == "25.0%"

    def test_percentage_value_not_multiplied(self):
        result = DataFormatter.format_percentage(75.5)
        assert result == "75.5%"

    def test_zero_is_zero(self):
        assert DataFormatter.format_percentage(0.0) == "0.0%"

    def test_one_is_100_percent(self):
        assert DataFormatter.format_percentage(1.0) == "100.0%"

    def test_custom_decimals(self):
        result = DataFormatter.format_percentage(0.1234, decimals=2)
        assert "12.34" in result


# ===========================================================================
# format_coordinates
# ===========================================================================

class TestFormatCoordinates:

    def test_none_lat_returns_na(self):
        assert DataFormatter.format_coordinates(None, -0.1) == "N/A"

    def test_none_lon_returns_na(self):
        assert DataFormatter.format_coordinates(51.5, None) == "N/A"

    def test_positive_lat_lon(self):
        result = DataFormatter.format_coordinates(51.5, 0.1)
        assert "N" in result
        assert "E" in result

    def test_negative_lat_lon(self):
        result = DataFormatter.format_coordinates(-33.86, -70.65)
        assert "S" in result
        assert "W" in result

    def test_result_format(self):
        result = DataFormatter.format_coordinates(51.5074, -0.1278)
        assert "°N" in result
        assert "°W" in result


# ===========================================================================
# format_date
# ===========================================================================

class TestFormatDate:

    def test_empty_string_returns_unknown(self):
        assert DataFormatter.format_date("") == "Unknown"

    def test_unknown_string_returns_unknown(self):
        assert DataFormatter.format_date("Unknown") == "Unknown"

    def test_valid_date_reformatted(self):
        result = DataFormatter.format_date(
            "2025-03-07T10:30:00Z",
            input_format='%Y-%m-%dT%H:%M:%SZ',
            output_format='%Y-%m-%d %H:%M',
        )
        assert result == "2025-03-07 10:30"

    def test_invalid_date_returned_as_is(self):
        result = DataFormatter.format_date("not-a-date", input_format='%Y-%m-%d')
        assert result == "not-a-date"


# ===========================================================================
# format_address
# ===========================================================================

class TestFormatAddress:

    def test_empty_dict_returns_na(self):
        assert DataFormatter.format_address({}) == "N/A"

    def test_none_returns_na(self):
        assert DataFormatter.format_address(None) == "N/A"

    def test_full_address(self):
        addr = {
            'building_number': '42',
            'street_name': 'Fleet Street',
            'town_city': 'London',
            'post_code': 'EC4Y 1BJ',
        }
        result = DataFormatter.format_address(addr)
        assert "42 Fleet Street" in result
        assert "London" in result
        assert "EC4Y 1BJ" in result

    def test_partial_address_no_building_number(self):
        addr = {'street_name': 'Oxford Street', 'town_city': 'London'}
        result = DataFormatter.format_address(addr)
        assert "Oxford Street" in result

    def test_missing_all_fields_returns_na(self):
        result = DataFormatter.format_address({'irrelevant_field': 'x'})
        assert result == "N/A"


# ===========================================================================
# format_property_age
# ===========================================================================

class TestFormatPropertyAge:

    def test_none_returns_unknown(self):
        assert DataFormatter.format_property_age(None) == "Unknown"

    def test_unknown_string_returns_unknown(self):
        assert DataFormatter.format_property_age("Unknown") == "Unknown"

    def test_very_old_property_high_risk(self):
        result = DataFormatter.format_property_age(1850)
        assert "High Risk" in result

    def test_mid_century_medium_risk(self):
        result = DataFormatter.format_property_age(1960)
        assert "Medium Risk" in result

    def test_modern_property_low_risk(self):
        result = DataFormatter.format_property_age(2010)
        assert "Low Risk" in result

    def test_non_numeric_returns_unknown(self):
        assert DataFormatter.format_property_age("Victorian") == "Unknown"


# ===========================================================================
# format_distance
# ===========================================================================

class TestFormatDistance:

    def test_none_returns_na(self):
        assert DataFormatter.format_distance(None) == "N/A"

    def test_km_unit_large_distance(self):
        result = DataFormatter.format_distance(5.0)
        assert "km" in result

    def test_sub_km_uses_meters(self):
        result = DataFormatter.format_distance(0.5)
        assert "m" in result

    def test_explicit_m_unit(self):
        result = DataFormatter.format_distance(2.5, unit="m")
        assert "m" in result


# ===========================================================================
# format_wind_speed
# ===========================================================================

class TestFormatWindSpeed:

    def test_ms_unit(self):
        result = DataFormatter.format_wind_speed(3.0, 4.0)
        assert "m/s" in result
        assert "5.0" in result  # sqrt(9+16) = 5

    def test_mph_unit(self):
        result = DataFormatter.format_wind_speed(3.0, 4.0, unit="mph")
        assert "mph" in result

    def test_invalid_input_returns_na(self):
        result = DataFormatter.format_wind_speed("a", "b")
        assert result == "N/A"


# ===========================================================================
# format_pressure
# ===========================================================================

class TestFormatPressure:

    def test_hpa_conversion(self):
        result = DataFormatter.format_pressure(101325.0, unit="hPa")
        assert "hPa" in result
        assert "1013" in result

    def test_mb_conversion(self):
        result = DataFormatter.format_pressure(101325.0, unit="mb")
        assert "mb" in result

    def test_pa_unit(self):
        result = DataFormatter.format_pressure(101325.0, unit="Pa")
        assert "Pa" in result

    def test_invalid_returns_na(self):
        result = DataFormatter.format_pressure("bad")
        assert result == "N/A"


# ===========================================================================
# format_precipitation
# ===========================================================================

class TestFormatPrecipitation:

    def test_mm_conversion(self):
        result = DataFormatter.format_precipitation(0.025)
        assert "mm" in result
        assert "25.0" in result

    def test_inches_conversion(self):
        result = DataFormatter.format_precipitation(0.025, unit="in")
        assert "in" in result

    def test_invalid_returns_na(self):
        result = DataFormatter.format_precipitation("bad")
        assert result == "N/A"


# ===========================================================================
# Backward-compat aliases
# ===========================================================================

class TestBackwardCompatAliases:

    def test_safe_format_float_alias(self):
        from visual.utils.formatters import safe_format_float
        assert safe_format_float(3.0) == DataFormatter.safe_format_float(3.0)

    def test_format_currency_alias(self):
        from visual.utils.formatters import format_currency
        assert format_currency(1000) == DataFormatter.format_currency(1000)

    def test_format_percentage_alias(self):
        from visual.utils.formatters import format_percentage
        assert format_percentage(0.5) == DataFormatter.format_percentage(0.5)

    def test_format_coordinates_alias(self):
        from visual.utils.formatters import format_coordinates
        assert format_coordinates(51.5, -0.1) == DataFormatter.format_coordinates(51.5, -0.1)

    def test_format_address_alias(self):
        from visual.utils.formatters import format_address
        assert format_address({}) == DataFormatter.format_address({})
