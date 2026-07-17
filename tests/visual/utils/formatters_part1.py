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
Tests for visual.utils.formatters — DataFormatter class (part 1).

safe_format_float, format_currency, format_percentage, format_coordinates.
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
