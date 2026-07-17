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
Tests for PopupBuilder formatting methods:
- safe_format_float
- format_currency
- format_percentage
- get_risk_color
"""


# ===========================================================================
# safe_format_float
# ===========================================================================

class TestSafeFormatFloat:

    def test_none_returns_na(self, builder):
        assert builder.safe_format_float(None) == "N/A"

    def test_na_string_returns_na(self, builder):
        assert builder.safe_format_float("N/A") == "N/A"

    def test_empty_string_returns_na(self, builder):
        assert builder.safe_format_float("") == "N/A"

    def test_integer_formatted(self, builder):
        result = builder.safe_format_float(42)
        assert result == "42.00"

    def test_float_formatted_default_decimals(self, builder):
        result = builder.safe_format_float(3.14159)
        assert result == "3.14"

    def test_float_formatted_custom_decimals(self, builder):
        result = builder.safe_format_float(3.14159, decimals=4)
        assert result == "3.1416"

    def test_zero_decimals(self, builder):
        result = builder.safe_format_float(3.7, decimals=0)
        assert result == "4"

    def test_negative_float(self, builder):
        result = builder.safe_format_float(-1.5)
        assert result == "-1.50"

    def test_string_numeric_value(self, builder):
        result = builder.safe_format_float("2.718")
        assert result == "2.72"

    def test_non_numeric_string_returned_as_is(self, builder):
        result = builder.safe_format_float("abc")
        assert result == "abc"

    def test_zero_value(self, builder):
        result = builder.safe_format_float(0)
        assert result == "0.00"

    def test_large_number(self, builder):
        result = builder.safe_format_float(1_000_000.0)
        assert result == "1000000.00"

    def test_list_not_convertible_returns_as_str(self, builder):
        result = builder.safe_format_float([1, 2, 3])
        # TypeError caught, returns str([1,2,3])
        assert result == str([1, 2, 3])


# ===========================================================================
# format_currency
# ===========================================================================

class TestFormatCurrency:

    def test_none_returns_not_available(self, builder):
        assert builder.format_currency(None) == "Not available"

    def test_na_string_returns_not_available(self, builder):
        assert builder.format_currency("N/A") == "Not available"

    def test_empty_string_returns_not_available(self, builder):
        assert builder.format_currency("") == "Not available"

    def test_unknown_string_returns_not_available(self, builder):
        assert builder.format_currency("Unknown") == "Not available"

    def test_integer_formatted_with_pound(self, builder):
        result = builder.format_currency(1000)
        assert result == "\u00a31,000.00"

    def test_float_formatted_with_pound(self, builder):
        result = builder.format_currency(1234.56)
        assert result == "\u00a31,234.56"

    def test_large_amount(self, builder):
        result = builder.format_currency(1_000_000)
        assert result == "\u00a31,000,000.00"

    def test_zero_amount(self, builder):
        result = builder.format_currency(0)
        assert result == "\u00a30.00"

    def test_negative_amount(self, builder):
        result = builder.format_currency(-500)
        assert result == "\u00a3-500.00"

    def test_string_numeric_amount(self, builder):
        result = builder.format_currency("750000")
        assert result == "\u00a3750,000.00"

    def test_custom_symbol_dollar(self, builder):
        result = builder.format_currency(100, symbol="$")
        assert result == "$100.00"

    def test_custom_symbol_euro(self, builder):
        result = builder.format_currency(200, symbol="\u20ac")
        assert result == "\u20ac200.00"

    def test_non_numeric_string_returned_as_is(self, builder):
        result = builder.format_currency("not_a_number")
        assert result == "not_a_number"


# ===========================================================================
# format_percentage
# ===========================================================================

class TestFormatPercentage:

    def test_none_returns_na(self, builder):
        assert builder.format_percentage(None) == "N/A"

    def test_na_string_returns_na(self, builder):
        assert builder.format_percentage("N/A") == "N/A"

    def test_empty_string_returns_na(self, builder):
        assert builder.format_percentage("") == "N/A"

    def test_decimal_less_than_1_multiplied_by_100(self, builder):
        result = builder.format_percentage(0.5)
        assert result == "50.0%"

    def test_decimal_zero(self, builder):
        result = builder.format_percentage(0.0)
        assert result == "0.0%"

    def test_decimal_close_to_1(self, builder):
        result = builder.format_percentage(0.999)
        assert "99.9" in result

    def test_value_exactly_1_treated_as_percentage(self, builder):
        # 1 is not < 1, so formatted as-is with decimals
        result = builder.format_percentage(1.0)
        assert result == "1.0%"

    def test_value_greater_than_1_not_multiplied(self, builder):
        result = builder.format_percentage(75.0)
        assert result == "75.0%"

    def test_value_100_formatted(self, builder):
        result = builder.format_percentage(100)
        assert result == "100.0%"

    def test_custom_decimals_zero(self, builder):
        result = builder.format_percentage(0.5, decimals=0)
        assert result == "50%"

    def test_custom_decimals_two(self, builder):
        result = builder.format_percentage(0.5, decimals=2)
        assert result == "50.00%"

    def test_string_numeric_decimal(self, builder):
        result = builder.format_percentage("0.25")
        assert result == "25.0%"

    def test_string_percentage(self, builder):
        result = builder.format_percentage("75")
        assert result == "75.0%"

    def test_non_numeric_string_returned_as_is(self, builder):
        result = builder.format_percentage("not_a_number")
        assert result == "not_a_number"

    def test_negative_decimal(self, builder):
        result = builder.format_percentage(-0.1)
        # -0.1 < 1, so multiplied by 100 = -10.0%
        assert "-10.0%" in result


# ===========================================================================
# get_risk_color
# ===========================================================================

class TestGetRiskColor:

    def test_very_low_lowercase(self, builder):
        assert builder.get_risk_color("Very low") == "green"

    def test_very_low_titlecase(self, builder):
        assert builder.get_risk_color("Very Low") == "green"

    def test_low(self, builder):
        assert builder.get_risk_color("Low") == "lightgreen"

    def test_medium(self, builder):
        assert builder.get_risk_color("Medium") == "orange"

    def test_high(self, builder):
        assert builder.get_risk_color("High") == "red"

    def test_very_high_lowercase(self, builder):
        assert builder.get_risk_color("Very high") == "darkred"

    def test_very_high_titlecase(self, builder):
        assert builder.get_risk_color("Very High") == "darkred"

    def test_unknown_level_returns_blue(self, builder):
        assert builder.get_risk_color("Unknown") == "blue"

    def test_empty_string_returns_blue(self, builder):
        assert builder.get_risk_color("") == "blue"

    def test_none_returns_blue(self, builder):
        # None is not in the dict, so get() returns 'blue'
        assert builder.get_risk_color(None) == "blue"

    def test_arbitrary_string_returns_blue(self, builder):
        assert builder.get_risk_color("Catastrophic") == "blue"

    def test_all_defined_levels_return_string(self, builder):
        for level in ("Very low", "Very Low", "Low", "Medium", "High", "Very high", "Very High"):
            color = builder.get_risk_color(level)
            assert isinstance(color, str)
            assert len(color) > 0
