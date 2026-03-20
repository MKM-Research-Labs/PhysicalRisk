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
Tests for PropertyLayer._get_flood_frequency_label and _get_property_icon.
"""

import pytest
import folium

from visual.layer.property_layer.layer import PropertyLayer


class TestGetFloodFrequencyLabel:

    def test_zero_is_low(self):
        assert PropertyLayer._get_flood_frequency_label(0) == "Low"

    def test_count_1_is_medium(self):
        assert PropertyLayer._get_flood_frequency_label(1) == "Medium"

    def test_count_5_is_medium(self):
        assert PropertyLayer._get_flood_frequency_label(5) == "Medium"

    def test_count_6_is_high(self):
        """flood_count > 5 → High."""
        assert PropertyLayer._get_flood_frequency_label(6) == "High"

    def test_large_count_is_high(self):
        assert PropertyLayer._get_flood_frequency_label(100) == "High"

    def test_boundary_exactly_1(self):
        assert PropertyLayer._get_flood_frequency_label(1) == "Medium"

    def test_boundary_exactly_5(self):
        assert PropertyLayer._get_flood_frequency_label(5) == "Medium"


class TestGetPropertyIcon:

    def _layer(self, flood_count=0):
        layer = PropertyLayer()
        layer._property_hazard = {}
        if flood_count > 0:
            layer._property_hazard["PROP-001"] = {"flood_count": flood_count}
        return layer

    def test_returns_folium_icon(self):
        layer = self._layer()
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert isinstance(icon, folium.Icon)

    def test_green_for_no_floods(self):
        """flood_count == 0 → green."""
        layer = self._layer(flood_count=0)
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert icon.options["marker_color"] == "green"

    def test_orange_for_medium_floods(self):
        """1 <= flood_count <= 5 → orange."""
        layer = self._layer(flood_count=3)
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert icon.options["marker_color"] == "orange"

    def test_red_for_high_floods(self):
        """flood_count > 5 → red."""
        layer = self._layer(flood_count=10)
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert icon.options["marker_color"] == "red"

    def test_mortgaged_uses_university_icon(self):
        """show_mortgage_status=True + has_mortgage → 'university' icon."""
        layer = self._layer()
        layer.show_mortgage_status = True
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=True)
        assert icon.options["icon"] == "university"

    def test_no_mortgage_uses_home_icon(self):
        layer = self._layer()
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert icon.options["icon"] == "home"

    def test_show_mortgage_status_false_uses_home_even_with_mortgage(self):
        """show_mortgage_status=False → home icon regardless of mortgage status."""
        layer = self._layer()
        layer.show_mortgage_status = False
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=True)
        assert icon.options["icon"] == "home"

    def test_unknown_property_id_gets_green(self):
        """Property not in _property_hazard → flood_count=0 → green."""
        layer = self._layer(flood_count=10)  # only for PROP-001
        icon = layer._get_property_icon({"property_id": "PROP-UNKNOWN"}, has_mortgage=False)
        assert icon.options["marker_color"] == "green"

    def test_boundary_flood_count_1_orange(self):
        """Boundary: flood_count == 1 → orange."""
        layer = self._layer(flood_count=1)
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert icon.options["marker_color"] == "orange"

    def test_boundary_flood_count_5_orange(self):
        """Boundary: flood_count == 5 → orange (not high)."""
        layer = self._layer(flood_count=5)
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert icon.options["marker_color"] == "orange"

    def test_no_property_hazard_attribute(self):
        """_property_hazard attribute missing (hasattr guard) → green."""
        layer = PropertyLayer()
        if hasattr(layer, '_property_hazard'):
            del layer._property_hazard
        icon = layer._get_property_icon({"property_id": "PROP-001"}, has_mortgage=False)
        assert isinstance(icon, folium.Icon)
