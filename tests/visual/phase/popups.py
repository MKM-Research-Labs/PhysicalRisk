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

"""Tests for popup builder modules: PopupBuilder, PropertyPopupBuilder, GaugePopupBuilder."""

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
        self.sample_mortgage_risk = {
            'MortgageID': 'MTG-test-001',
            'PropertyID': 'PROP-test-001',
            'loan_amount': 500000,
            'interest_rate': 0.035,
            'monthly_payment': 2465.87,
            'annual_payment': 29590.44,
            'credit_spread': 0.005,
            'recovery_haircut': 0.20,
            'mortgage_value': 480000,
            'mortgage_value_at_risk': 96000,
            'flood_risk_level': 'Medium',
            'flood_risk_value': 0.25,
            'flood_depth': 0.3,
            'property_value': 750000
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

    def test_mortgage_section(self):
        section = self.builder.create_mortgage_section(self.sample_mortgage, 750000, 'Medium')
        assert 'MTG-test-001' in section
        assert 'Test Bank' in section
        assert '£500,000.00' in section
        assert 'MORTGAGE DETAILS' in section

    def test_mortgage_risk_section(self):
        section = self.builder.create_mortgage_risk_section(self.sample_mortgage_risk)
        assert 'MORTGAGE RISK ANALYSIS' in section
        assert 'MTG-test-001' in section
        assert '£480,000.00' in section
        assert 'Medium' in section

    def test_complete_popup_creation(self):
        popup = self.builder.create_complete_popup_content(
            self.sample_property, 'PROP-test-001', self.sample_address,
            '51.51°N, -0.13°E', 'Medium', 'Close', 2.5, False,
            750000, 1985, 'Medium (1925-1975)', True,
            self.sample_mortgage, self.sample_flood_info, self.sample_mortgage_risk
        )
        assert 'Property Analysis' in popup
        assert 'PROP-test-001' in popup
        assert 'font-family: Arial' in popup
        assert 'MORTGAGE DETAILS' in popup
        assert 'MORTGAGE RISK ANALYSIS' in popup

    def test_build_property_popup_returns_object(self):
        popup = self.builder.build_property_popup(
            self.sample_property, 'PROP-test-001', self.sample_address,
            '51.51°N, -0.13°E', 'Medium', 'Close', 2.5, False,
            750000, 1985, 'Medium (1925-1975)', True,
            self.sample_mortgage, self.sample_flood_info, self.sample_mortgage_risk
        )
        assert popup is not None


class TestGaugePopupBuilder:
    """Test GaugePopupBuilder section and popup creation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.popups import GaugePopupBuilder
        self.builder = GaugePopupBuilder()
        self.sample_gauge_info = {
            'SensorDetails': {
                'GaugeInformation': {
                    'GaugeOwner': 'Environment Agency',
                    'GaugeType': 'Water Level Gauge',
                    'OperationalStatus': 'Fully operational',
                    'DataSourceType': 'Automatic',
                    'InstallationDate': '2010-03-15',
                    'CertificationStatus': 'Certified'
                },
                'Measurements': {
                    'MeasurementFrequency': 'Every 15 minutes',
                    'MeasurementMethod': 'Pressure sensor',
                    'DataTransmission': 'Telemetry'
                }
            },
            'FloodStage': {
                'UK': {'FloodAlert': 1.5, 'FloodWarning': 2.0, 'SevereFloodWarning': 2.5}
            },
            'SensorStats': {
                'HistoricalHighLevel': 3.2,
                'HistoricalHighDate': '2014-02-07',
                'LastDateLevelExceedLevel3': '2020-12-25',
                'FrequencyExceedLevel3': 5
            }
        }
        self.sample_flood_info = {
            'max_level': 3.5,
            'alert_level': 1.5,
            'warning_level': 2.0,
            'severe_level': 2.5,
            'max_gauge_reading': 3.2
        }

    def test_status_color_operational(self):
        assert self.builder.get_status_color('Fully operational') == '#27AE60'

    def test_status_color_maintenance(self):
        assert self.builder.get_status_color('Maintenance required') == '#F39C12'

    def test_status_color_offline(self):
        assert self.builder.get_status_color('Temporarily offline') == '#C0392B'

    def test_location_description_central(self):
        assert 'Central London' in self.builder.determine_location_description(-0.1)

    def test_location_description_southeast(self):
        assert 'Southeast' in self.builder.determine_location_description(0.5)

    def test_location_description_east(self):
        assert 'East London' in self.builder.determine_location_description(0.1)

    def test_equipment_details_section(self):
        section = self.builder.create_equipment_details_section(self.sample_gauge_info)
        assert 'Environment Agency' in section
        assert 'Water Level Gauge' in section
        assert 'Fully operational' in section
        assert 'Equipment Details' in section

    def test_measurement_approach_section(self):
        section = self.builder.create_measurement_approach_section(self.sample_gauge_info)
        assert 'Every 15 minutes' in section
        assert 'Pressure sensor' in section
        assert 'Telemetry' in section
        assert 'Measurement Approach' in section

    def test_flood_thresholds_section(self):
        section = self.builder.create_flood_thresholds_section(self.sample_gauge_info)
        assert '1.50 m' in section
        assert '2.00 m' in section
        assert '2.50 m' in section
        assert 'Flood Thresholds' in section

    def test_historical_context_section(self):
        section = self.builder.create_historical_context_section(self.sample_gauge_info)
        assert '3.20 m' in section
        assert '2014-02-07' in section
        assert '5 times' in section
        assert 'Historical Context' in section

    def test_flood_risk_data_section(self):
        section = self.builder.create_flood_risk_data_section(self.sample_flood_info)
        assert '3.50 m' in section
        assert 'Max Level' in section
        assert 'Flood Risk Data' in section

    def test_complete_gauge_popup(self):
        popup = self.builder.create_complete_gauge_popup_content(
            'GAUGE-test-001', 51.4975, 0.1, self.sample_gauge_info, self.sample_flood_info
        )
        assert 'Flood Gauge Analysis' in popup
        assert 'GAUGE-test-001' in popup
        assert 'East London' in popup
        assert 'font-family: Arial' in popup

    def test_tooltip_creation(self):
        tooltip = self.builder.create_gauge_tooltip('Water Level Gauge', 'Fully operational', 1.5)
        assert 'Water Level Gauge' in tooltip
        assert 'Fully operational' in tooltip
        assert '1.50m' in tooltip

    def test_build_gauge_popup_returns_object(self):
        popup = self.builder.build_gauge_popup(
            'GAUGE-test-001', 51.4975, 0.1, self.sample_gauge_info, self.sample_flood_info
        )
        assert popup is not None


class TestPopupIntegration:
    """Test consistency between PopupBuilder subclasses."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.popups import GaugePopupBuilder, PopupBuilder, PropertyPopupBuilder
        self.prop_builder = PropertyPopupBuilder()
        self.gauge_builder = GaugePopupBuilder()
        self.base_builder = PopupBuilder()

    def test_currency_formatting_consistent(self):
        assert self.prop_builder.format_currency(1000) == self.gauge_builder.format_currency(1000)

    def test_float_formatting_consistent(self):
        assert (self.prop_builder.safe_format_float(3.14159) ==
                self.gauge_builder.safe_format_float(3.14159))

    def test_risk_color_consistent(self):
        assert (self.prop_builder.get_risk_color('High') ==
                self.gauge_builder.get_risk_color('High'))

    def test_section_background_consistent(self):
        prop_section = self.prop_builder.create_section("Test", "<p>Content</p>")
        gauge_section = self.gauge_builder.create_section("Test", "<p>Content</p>")
        assert 'background-color: #EBF5FB' in prop_section
        assert 'background-color: #EBF5FB' in gauge_section

    def test_inheritance_from_base(self):
        from visual.popups import PopupBuilder
        assert isinstance(self.prop_builder, PopupBuilder)
        assert isinstance(self.gauge_builder, PopupBuilder)


class TestPopupErrorHandling:
    """Test graceful handling of None/empty/malformed data."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from visual.popups import GaugePopupBuilder, PopupBuilder, PropertyPopupBuilder
        self.builder = PopupBuilder()
        self.prop_builder = PropertyPopupBuilder()
        self.gauge_builder = GaugePopupBuilder()

    def test_base_safe_format_float_none(self):
        assert self.builder.safe_format_float(None) == "N/A"

    def test_base_format_currency_none(self):
        assert self.builder.format_currency(None) == "Not available"

    def test_base_format_percentage_none(self):
        assert self.builder.format_percentage(None) == "N/A"

    def test_property_empty_flood_info(self):
        result = self.prop_builder.create_flood_info_section({})
        assert result == ""

    def test_property_empty_mortgage_risk(self):
        result = self.prop_builder.create_mortgage_risk_section({})
        assert result == ""

    def test_gauge_empty_flood_data(self):
        result = self.gauge_builder.create_flood_risk_data_section({})
        assert result == ""

    def test_property_incomplete_data_no_crash(self):
        incomplete_property = {'PropertyHeader': {}}
        section = self.prop_builder.create_property_section(
            incomplete_property, 'TEST', {}, '', 2000, 'New', 100000, False
        )
        assert 'Unknown' in section

    def test_gauge_incomplete_data_no_crash(self):
        incomplete_gauge = {'SensorDetails': {}}
        section = self.gauge_builder.create_equipment_details_section(incomplete_gauge)
        assert 'Unknown' in section
