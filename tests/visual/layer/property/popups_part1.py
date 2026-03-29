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
Tests for PropertyLayer popup methods — part 1.

_create_property_popup, _create_flood_risk_section.
"""

import pytest

from visual.layer.property_layer.layer import PropertyLayer

from .conftest import make_property_info, make_mortgage_info


# ===========================================================================
# _create_property_popup
# ===========================================================================

class TestCreatePropertyPopup:

    def test_returns_html_string(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(), {}, False, {}, None)
        assert isinstance(html, str)
        assert "<div" in html

    def test_contains_property_id(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info("PROP-007"), {}, False, {}, None)
        assert "PROP-007" in html

    def test_contains_address(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(), {}, False, {}, None)
        assert "Main St" in html

    def test_contains_property_details_section(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(), {}, False, {}, None)
        assert "Property Details" in html
        assert "Detached" in html

    def test_coordinates_formatted(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(lat=51.5, lon=-0.1), {}, False, {}, None)
        assert "51.5" in html

    def test_coords_none_shows_na(self):
        """lat/lon both None -> coord_str = 'N/A'."""
        layer = PropertyLayer()
        info = make_property_info()
        info["coordinates"] = {"latitude": None, "longitude": None}
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "N/A" in html

    def test_river_distance_formatted(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(river_dist=300), {}, False, {}, None)
        assert "300" in html

    def test_river_distance_na_string(self):
        """river_dist = 'N/A' -> shown as 'N/A'."""
        layer = PropertyLayer()
        info = make_property_info()
        info["river_distance_m"] = "N/A"
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "N/A" in html

    def test_river_distance_none(self):
        """river_dist = None -> shown as 'N/A'."""
        layer = PropertyLayer()
        info = make_property_info()
        info["river_distance_m"] = None
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "N/A" in html

    def test_mortgage_section_included_when_has_mortgage(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(
            make_property_info(), {}, True, make_mortgage_info(), None
        )
        assert "MORTGAGE DETAILS" in html

    def test_mortgage_section_excluded_when_no_mortgage(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(), {}, False, {}, None)
        assert "MORTGAGE DETAILS" not in html

    def test_elevation_section(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(make_property_info(ground_elevation=4.5), {}, False, {}, None)
        assert "Elevation" in html

    def test_valuation_current_value(self):
        layer = PropertyLayer()
        info = make_property_info()
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "Current Value" in html


# ===========================================================================
# _create_flood_risk_section
# ===========================================================================

class TestCreateFloodRiskSection:

    def test_returns_html_string(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({
            "risk_level": "High", "property_elevation": 4.0,
            "water_level": 5.0, "flood_depth": 1.0, "value_at_risk": 50_000,
        })
        assert isinstance(section, str)
        assert "<div" in section

    def test_includes_risk_level(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({"risk_level": "High"})
        assert "High" in section

    def test_empty_flood_info(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({})
        assert isinstance(section, str)
        assert "Unknown" in section

    def test_includes_flood_assessment_section(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({"risk_level": "Low"})
        assert "Flood Risk Assessment" in section

    def test_numeric_values_formatted(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({
            "risk_level": "Medium", "flood_depth": 0.75, "value_at_risk": 25_000
        })
        assert "0.75" in section
