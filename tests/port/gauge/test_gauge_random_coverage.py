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

"""Coverage expansion tests for gauge_random.py — missing lines.

Lines: 176-177, 243, 329-331, 385, 400
"""

import pytest

from port.rand.thames.gauge.gauge_random import (
    generate_date_value,
    generate_decimal_value,
    generate_field_value,
    generate_gauge_metadata,
    generate_integer_value,
    generate_menu_value,
    generate_text_value,
)


@pytest.fixture
def metadata():
    """Minimal metadata dict for gauge random tests."""
    return {
        "gauge_id": "GAUGE-TEST",
        "historical_high_level": 6.5,
        "historical_high_date": "2022-06-01",
        "flood_alert": 3.9,
        "flood_warning": 5.2,
        "severe_flood_warning": 6.175,
        "install_date": "2015-01-01",
        "location": {
            "lat": 51.5, "lon": -0.1, "elevation": 7.5,
            "name": "", "area": "Westminster",
        },
        "catchment_name": "Thames",
        "index": 0,
    }


class TestGaugeNameFallback:
    """Lines 176-177: GaugeName when location has no short_name."""

    def test_empty_name_falls_back_to_area(self, metadata):
        """When name is empty, uses area_name."""
        result = generate_text_value("GaugeName", {}, 0, metadata)
        assert "Westminster" in result
        assert "Thames" in result

    def test_no_name_key_falls_back_to_area(self, metadata):
        metadata["location"] = {"lat": 51.5, "lon": -0.1, "elevation": 7.5, "area": "Putney"}
        result = generate_text_value("GaugeName", {}, 2, metadata)
        assert "Putney" in result


class TestIntegerDefault:
    """Line 243: unknown integer field returns randint."""

    def test_unknown_integer_field_returns_int(self, metadata):
        result = generate_integer_value("UnknownIntField", {"type": "integer"}, 0, metadata)
        assert isinstance(result, int)
        assert 1 <= result <= 10


class TestMenuOptionsDefault:
    """Lines 329-331: unknown menu field with options list uses index cycling."""

    def test_unknown_menu_with_options_cycles(self, metadata):
        field_def = {"type": "menu", "options": ["OptionA", "OptionB", "OptionC"]}
        result = generate_menu_value("UnknownMenuField", field_def, 1, metadata)
        assert result == "OptionB"

    def test_unknown_menu_with_options_wraps(self, metadata):
        field_def = {"type": "menu", "options": ["X", "Y"]}
        result = generate_menu_value("UnknownMenuField", field_def, 4, metadata)
        assert result == "X"  # 4 % 2 = 0

    def test_unknown_menu_no_options_returns_empty(self, metadata):
        result = generate_menu_value("UnknownMenuField", {"type": "menu"}, 0, metadata)
        assert result == ""


class TestFieldValueNonDictDef:
    """Line 385: field_def is not a dict."""

    def test_string_field_def_returned_as_is(self, metadata):
        result = generate_field_value("SomeField", "literal_value", 0, metadata)
        assert result == "literal_value"

    def test_numeric_field_def_returns_empty_string(self, metadata):
        result = generate_field_value("SomeField", 42, 0, metadata)
        assert result == ""

    def test_none_field_def_returns_empty_string(self, metadata):
        result = generate_field_value("SomeField", None, 0, metadata)
        assert result == ""


class TestFieldValueUnknownType:
    """Line 400: unknown field type returns empty string."""

    def test_unknown_type_returns_empty(self, metadata):
        result = generate_field_value("SomeField", {"type": "blob"}, 0, metadata)
        assert result == ""

    def test_no_type_defaults_to_text(self, metadata):
        result = generate_field_value("SomeField", {"no_type_key": True}, 0, metadata)
        # Default type is 'text', returns Text-SomeField-0
        assert "SomeField" in result
