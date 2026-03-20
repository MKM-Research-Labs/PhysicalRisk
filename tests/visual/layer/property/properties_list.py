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
Tests for PropertyLayer._get_properties_list — all key format variants.
"""

import pytest
from unittest.mock import patch

from visual.layer.property_layer.layer import PropertyLayer


def _make_property(property_id="PROP-001"):
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": property_id},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
        }
    }


class TestGetPropertiesList:

    def test_items_key(self):
        layer = PropertyLayer()
        result = layer._get_properties_list({"items": [_make_property()]})
        assert len(result) == 1

    def test_properties_key(self):
        layer = PropertyLayer()
        result = layer._get_properties_list({"properties": [_make_property()]})
        assert len(result) == 1

    def test_property_header_single_dict(self):
        """Dict with 'PropertyHeader' key wrapped as single-item list."""
        layer = PropertyLayer()
        prop = _make_property()
        result = layer._get_properties_list(prop)
        assert len(result) == 1
        assert result[0] is prop

    def test_portfolio_fallback(self):
        """'portfolio' key used when no items/properties/PropertyHeader."""
        layer = PropertyLayer()
        result = layer._get_properties_list({"portfolio": [_make_property()]})
        assert len(result) == 1

    def test_list_input(self):
        layer = PropertyLayer()
        result = layer._get_properties_list([_make_property()])
        assert len(result) == 1

    def test_empty_dict_returns_empty_list(self):
        layer = PropertyLayer()
        assert layer._get_properties_list({}) == []

    def test_empty_items_returns_empty_list(self):
        layer = PropertyLayer()
        assert layer._get_properties_list({"items": []}) == []

    def test_non_dict_non_list_returns_empty(self):
        """Unexpected type (e.g., string) → empty list."""
        layer = PropertyLayer()
        assert layer._get_properties_list("not_a_dict") == []

    def test_none_input_returns_empty(self):
        layer = PropertyLayer()
        assert layer._get_properties_list(None) == []

    def test_integer_returns_empty(self):
        layer = PropertyLayer()
        assert layer._get_properties_list(42) == []

    def test_multiple_items(self):
        layer = PropertyLayer()
        result = layer._get_properties_list({"items": [_make_property("P1"), _make_property("P2")]})
        assert len(result) == 2

    def test_items_key_takes_priority_over_properties(self):
        """'items' key used when both present (or properties is empty)."""
        layer = PropertyLayer()
        result = layer._get_properties_list({"items": [_make_property("P1")]})
        assert len(result) == 1
        assert result[0]["PropertyHeader"]["Header"]["PropertyID"] == "P1"


# ===========================================================================
# get_property_statistics — exception path
# ===========================================================================

class MockLoadedData:
    def __init__(self):
        self.property_flood_info = {}
        self.mortgage_lookup = {}


class TestGetPropertyStatistics:

    def test_empty_returns_empty_dict(self):
        """Empty property list → empty dict."""
        assert PropertyLayer().get_property_statistics([], MockLoadedData()) == {}

    def test_exception_in_loop_skipped(self):
        """Lines 456-457: exception in loop → caught, total_properties still counted."""
        layer = PropertyLayer()
        props = [{"dummy": True}]
        loaded = MockLoadedData()
        with patch("visual.layer.property_layer.layer.DataExtractor.extract_property_info",
                   side_effect=RuntimeError("extract failure")):
            result = layer.get_property_statistics(props, loaded)
        assert result["total_properties"] == 1
        assert result["mortgaged_properties"] == 0
