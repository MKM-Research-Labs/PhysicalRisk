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

"""Tests for create_property_section and create_flood_info_section."""

import pytest


# ---------------------------------------------------------------------------
# create_property_section
# ---------------------------------------------------------------------------

class TestCreatePropertySection:

    def test_contains_property_type(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'Residential' in html

    def test_contains_building_type(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'Terraced House' in html

    def test_contains_street_name(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'Flood Lane' in html

    def test_contains_town(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'London' in html

    def test_contains_postcode_when_present(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'SW1A 2AA' in html

    def test_no_postcode_when_absent(self, builder, prop, address_no_postcode):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address_no_postcode, '51.7°N, -1.3°E',
            2005, 'New (post-1991)', 300000, False
        )
        assert 'River Road' in html
        assert 'Oxford' in html

    def test_contains_coordinates(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5074°N, -0.1278°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert '51.5074' in html

    def test_contains_construction_year(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1975, 'Medium (1925-1975)', 450000, False
        )
        assert '1975' in html

    def test_contains_age_factor(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1975, 'Medium (1925-1975)', 450000, False
        )
        assert 'Medium (1925-1975)' in html

    def test_contains_construction_type(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'Brick' in html

    def test_contains_number_of_storeys(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert '2' in html

    def test_property_value_formatted_as_currency(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 500000, False
        )
        assert '500,000' in html

    def test_missing_header_fields_fall_back_to_unknown(self, builder, address):
        sparse_prop = {'PropertyHeader': {}}
        html = builder.create_property_section(
            sparse_prop, 'PROP-x', address, '0°N, 0°E', None, 'Unknown', 0, False
        )
        assert 'Unknown' in html

    def test_section_title_present(self, builder, prop, address):
        html = builder.create_property_section(
            prop, 'PROP-aabbccdd', address, '51.5°N, -0.1°E',
            1990, 'New (post-1991)', 450000, False
        )
        assert 'Property Information' in html


# ---------------------------------------------------------------------------
# create_flood_info_section
# ---------------------------------------------------------------------------

class TestCreateFloodInfoSection:

    def test_returns_empty_for_none(self, builder):
        assert builder.create_flood_info_section(None) == ""

    def test_returns_empty_for_empty_dict(self, builder):
        assert builder.create_flood_info_section({}) == ""

    def test_contains_gauge_name(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert 'Chelsea Gauge' in html

    def test_contains_distance(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert '0.80' in html

    def test_contains_water_level(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert '3.20' in html

    def test_contains_flood_depth(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert '0.50' in html

    def test_contains_risk_level(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert 'High' in html

    def test_contains_value_at_risk_formatted(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert '250,000' in html

    def test_section_title_present(self, builder, flood_info):
        html = builder.create_flood_info_section(flood_info)
        assert 'Flood Risk' in html

    def test_missing_optional_fields_show_na(self, builder):
        minimal = {'risk_level': 'Low', 'nearest_gauge': 'Test'}
        html = builder.create_flood_info_section(minimal)
        assert 'N/A' in html
