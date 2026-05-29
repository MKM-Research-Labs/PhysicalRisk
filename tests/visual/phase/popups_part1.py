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

"""Tests for popup builder modules — part 1: imports, base, and property popup."""

import pytest


class TestPopupImports:
    """Test that all popup modules can be imported and instantiated."""

    def test_popup_builder_import(self):
        from visual.popups import PopupBuilder
        assert PopupBuilder() is not None

    def test_property_popup_builder_import(self):
        from visual.popups import PropertyPopupBuilder
        assert PropertyPopupBuilder() is not None

    def test_gauge_popup_builder_import(self):
        from visual.popups import GaugePopupBuilder
        assert GaugePopupBuilder() is not None


class TestPopupBuilderBase:
    """Test base PopupBuilder formatting methods."""

    @pytest.fixture(autouse=True)
    def builder(self):
        from visual.popups import PopupBuilder
        self.builder = PopupBuilder()

    def test_safe_format_float_valid(self):
        assert self.builder.safe_format_float(3.14159, 2) == "3.14"

    def test_safe_format_float_none(self):
        assert self.builder.safe_format_float(None) == "N/A"

    def test_safe_format_float_invalid(self):
        assert self.builder.safe_format_float("invalid") == "invalid"

    def test_format_currency_valid(self):
        assert self.builder.format_currency(1000000) == "£1,000,000.00"

    def test_format_currency_none(self):
        assert self.builder.format_currency(None) == "Not available"

    def test_format_currency_invalid(self):
        assert self.builder.format_currency("invalid") == "invalid"

    def test_format_percentage_decimal(self):
        assert self.builder.format_percentage(0.85) == "85.0%"

    def test_format_percentage_whole(self):
        assert self.builder.format_percentage(85) == "85.0%"

    def test_format_percentage_none(self):
        assert self.builder.format_percentage(None) == "N/A"

    def test_risk_color_high(self):
        assert self.builder.get_risk_color('High') == 'red'

    def test_risk_color_low(self):
        assert self.builder.get_risk_color('Low') == 'lightgreen'

    def test_risk_color_unknown(self):
        assert self.builder.get_risk_color('Unknown') == 'blue'

    def test_create_section(self):
        section = self.builder.create_section("Test Section", "<p>Test content</p>")
        assert "Test Section" in section
        assert "Test content" in section
        assert "background-color: #EBF5FB" in section

    def test_create_data_row(self):
        row = self.builder.create_data_row("Test Label", "Test Value")
        assert "Test Label:" in row
        assert "Test Value" in row
        assert "<p>" in row

    def test_create_colored_text(self):
        colored = self.builder.create_colored_text("High Risk", "red", bold=True)
        assert "color: red" in colored
        assert "font-weight: bold" in colored
        assert "High Risk" in colored

    def test_create_popup_wrapper(self):
        wrapper = self.builder.create_popup_wrapper("<p>Content</p>", 400, 500)
        assert "font-family: Arial" in wrapper
        assert "width: 400px" in wrapper
        assert "max-height: 500px" in wrapper


class TestPropertyPopupBuilder:
    """Test PropertyPopupBuilder section and popup creation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.popups import PropertyPopupBuilder
        self.builder = PropertyPopupBuilder()
        self.sample_property = {
            'PropertyHeader': {
                'Header': {
                    'PropertyID': 'PROP-test-001',
                    'propertyType': 'Residential',
                    'propertyStatus': 'Active'
                },
                'PropertyAttributes': {
                    'PropertyType': 'Terraced House',
                    'NumberOfStoreys': 2,
                    'ConstructionYear': 1985
                },
                'Construction': {'ConstructionType': 'Brick'},
                'Location': {
                    'LatitudeDegrees': 51.5074,
                    'LongitudeDegrees': -0.1278,
                    'BuildingNumber': '123',
                    'StreetName': 'Test Street',
                    'TownCity': 'London',
                    'Postcode': 'SW1A 1AA'
                }
            }
        }
        self.sample_address = {
            'building_number': '123',
            'street_name': 'Test Street',
            'town_city': 'London',
            'post_code': 'SW1A 1AA'
        }
        self.sample_mortgage = {
            'Header': {'MortgageID': 'MTG-test-001'},
            'FinancialTerms': {
                'OriginalLoan': 500000,
                'OriginalLendingRate': 0.035,
                'TermYears': 25
            },
            'Application': {'MortgageProvider': 'Test Bank'}
        }
        self.sample_flood_info = {
            'nearest_gauge': 'Thames Test Gauge',
            'distance_to_gauge': 2.5,
            'water_level': 1.2,
            'flood_depth': 0.3,
            'risk_value': 0.25,
            'risk_level': 'Medium',
            'value_at_risk': 125000
        }

    def test_property_section_contains_type(self):
        section = self.builder.create_property_section(
            self.sample_property, 'PROP-test-001', self.sample_address,
            '51.51°N, -0.13°E', 1985, 'Medium (1925-1975)', 750000, True
        )
        assert 'Residential' in section
        assert 'Terraced House' in section

    def test_property_section_contains_address(self):
        section = self.builder.create_property_section(
            self.sample_property, 'PROP-test-001', self.sample_address,
            '51.51°N, -0.13°E', 1985, 'Medium (1925-1975)', 750000, True
        )
        assert '123 Test Street, London' in section
        assert '£750,000.00' in section

    def test_flood_info_section(self):
        section = self.builder.create_flood_info_section(self.sample_flood_info)
        assert 'Thames Test Gauge' in section
        assert 'Medium' in section
        assert '£125,000.00' in section
        assert '2.50 km' in section

    def test_rloan_section(self):
        section = self.builder.create_rloan_section(self.sample_mortgage, 750000, 'Medium')
        assert 'MTG-test-001' in section
        assert 'Test Bank' in section
        assert '£500,000.00' in section
        assert 'MORTGAGE DETAILS' in section

    def test_complete_popup_creation(self):
        popup = self.builder.create_complete_popup_content(
            self.sample_property, 'PROP-test-001', self.sample_address,
            '51.51°N, -0.13°E', 'Medium', 'Close', 2.5, False,
            750000, 1985, 'Medium (1925-1975)', True,
            self.sample_mortgage, self.sample_flood_info,
        )
        assert 'Property Analysis' in popup
        assert 'PROP-test-001' in popup
        assert 'font-family: Arial' in popup
        assert 'MORTGAGE DETAILS' in popup

    def test_build_property_popup_returns_object(self):
        popup = self.builder.build_property_popup(
            self.sample_property, 'PROP-test-001', self.sample_address,
            '51.51°N, -0.13°E', 'Medium', 'Close', 2.5, False,
            750000, 1985, 'Medium (1925-1975)', True,
            self.sample_mortgage, self.sample_flood_info,
        )
        assert popup is not None
