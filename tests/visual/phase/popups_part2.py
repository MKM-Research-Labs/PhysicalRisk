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

"""Tests for popup builder modules — part 2: gauge popup, integration, error handling."""

import pytest


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

    def _lon_bounds(self):
        from config.visual import get_catchment_bounds
        min_lon, _, max_lon, _ = get_catchment_bounds()
        return min_lon, max_lon

    def test_location_description_western(self):
        min_lon, max_lon = self._lon_bounds()
        lon = min_lon + 0.1 * (max_lon - min_lon)
        assert 'Western part of catchment' in self.builder.determine_location_description(lon)

    def test_location_description_central(self):
        min_lon, max_lon = self._lon_bounds()
        lon = min_lon + 0.5 * (max_lon - min_lon)
        assert 'Central part of catchment' in self.builder.determine_location_description(lon)

    def test_location_description_eastern(self):
        min_lon, max_lon = self._lon_bounds()
        lon = min_lon + 0.9 * (max_lon - min_lon)
        assert 'Eastern part of catchment' in self.builder.determine_location_description(lon)

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
        min_lon, max_lon = self._lon_bounds()
        eastern_lon = min_lon + 0.9 * (max_lon - min_lon)
        popup = self.builder.create_complete_gauge_popup_content(
            'GAUGE-test-001', 51.4975, eastern_lon, self.sample_gauge_info, self.sample_flood_info
        )
        assert 'Flood Gauge Analysis' in popup
        assert 'GAUGE-test-001' in popup
        assert 'Eastern part of catchment' in popup
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
