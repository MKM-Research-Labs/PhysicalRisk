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

"""Module integration tests using synthetic test data.

Tests how visual sub-modules work together with realistic data structures,
without requiring real data files or a running server.
"""

import pytest
import folium


# ---------------------------------------------------------------------------
# Synthetic test data (mirrors TestDataSetup from legacy test_integration.py)
# ---------------------------------------------------------------------------

GAUGE_DATA = {
    "flood_gauges": [
        {
            "FloodGauge": {
                "Header": {
                    "GaugeID": "TEST-GAUGE-001",
                    "GaugeName": "Test Thames Gauge",
                },
                "SensorDetails": {
                    "GaugeInformation": {
                        "GaugeLatitude": 51.5074,
                        "GaugeLongitude": -0.1278,
                        "GaugeOwner": "Environment Agency",
                        "GaugeType": "Water Level",
                        "OperationalStatus": "Fully operational",
                        "DataSourceType": "Telemetry",
                        "InstallationDate": "2020-01-01",
                        "CertificationStatus": "Certified",
                    },
                    "Measurements": {
                        "MeasurementFrequency": "15 minutes",
                        "MeasurementMethod": "Pressure sensor",
                        "DataTransmission": "Real-time",
                    },
                },
                "SensorStats": {
                    "HistoricalHighLevel": 5.2,
                    "HistoricalHighDate": "2020-02-09",
                    "LastDateLevelExceedLevel3": "2024-11-15",
                    "FrequencyExceedLevel3": 3,
                },
                "FloodStage": {
                    "UK": {
                        "FloodAlert": 2.5,
                        "FloodWarning": 3.5,
                        "SevereFloodWarning": 4.5,
                    }
                },
            }
        }
    ]
}

PROPERTY_DATA = {
    "properties": [
        {
            "PropertyHeader": {
                "Header": {
                    "PropertyID": "TEST-PROP-001",
                    "propertyType": "Residential",
                    "propertyStatus": "Active",
                },
                "PropertyAttributes": {
                    "PropertyType": "House",
                    "ConstructionYear": 1990,
                    "NumberOfStoreys": 2,
                },
                "Construction": {"ConstructionType": "Brick"},
                "Location": {
                    "LatitudeDegrees": 51.5074,
                    "LongitudeDegrees": -0.1278,
                    "BuildingNumber": "123",
                    "StreetName": "Test Street",
                    "TownCity": "London",
                    "Postcode": "SW1A 1AA",
                },
            },
            "FloodRisk": "Medium",
            "ThamesProximity": "Close",
            "GroundElevation": 10.0,
            "ElevationEstimated": False,
            "PropertyValue": 500000,
        }
    ]
}

MORTGAGE_DATA = {
    "mortgages": [
        {
            "PropertyID": "TEST-PROP-001",
            "Mortgage": {
                "Header": {
                    "MortgageID": "TEST-MTG-001",
                    "PropertyID": "TEST-PROP-001",
                },
                "FinancialTerms": {
                    "OriginalLoan": 400000,
                    "OriginalLendingRate": 0.035,
                    "TermYears": 25,
                    "LoanToValueRatio": 0.8,
                },
                "Application": {"MortgageProvider": "Test Bank Ltd"},
            },
        }
    ]
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCoreModuleIntegration:
    """Core modules must instantiate and expose expected APIs."""

    def test_data_loader_creation(self, tmp_path):
        from visual.core import DataLoader
        loader = DataLoader(tmp_path)
        assert loader is not None
        assert hasattr(loader, 'load_all_data')

    def test_map_builder_creates_map(self):
        from visual.core import MapBuilder
        builder = MapBuilder()
        m = builder.create_map(center=(51.5, -0.1), zoom=10)
        assert m is not None

    def test_tc_event_visualization_creation(self):
        from visual.core import TCEventVisualization
        viz = TCEventVisualization()
        assert viz is not None


class TestLayerIntegration:
    """Layer modules must instantiate and accept synthetic data."""

    def test_gauge_layer_creation(self):
        from visual.layer import GaugeLayer
        layer = GaugeLayer()
        assert layer is not None

    def test_property_layer_creation(self):
        from visual.layer import PropertyLayer
        layer = PropertyLayer()
        assert layer is not None

    def test_gauge_layer_has_add_method(self):
        from visual.layer import GaugeLayer
        layer = GaugeLayer()
        assert hasattr(layer, 'add_to_map') or hasattr(layer, 'add_gauges')

    def test_property_layer_has_add_method(self):
        from visual.layer import PropertyLayer
        layer = PropertyLayer()
        assert hasattr(layer, 'add_to_map') or hasattr(layer, 'add_properties')


class TestInteractivityIntegration:
    """Interactivity modules must wire up to folium maps."""

    def test_backend_and_context_on_same_map(self):
        from visual.interactivity.backend_handler import BackendHandler
        from visual.interactivity.context_menus import ContextMenuHandler
        test_map = folium.Map(location=[51.5074, -0.1278])
        BackendHandler().add_to_map(test_map)
        ContextMenuHandler().add_to_map(test_map)
        html = test_map.get_root().render()
        assert '__BACKEND_CONFIG' in html

    def test_interactivity_manager_full_setup(self):
        from visual.interactivity import InteractivityManager
        test_map = folium.Map(location=[51.5074, -0.1278])
        manager = InteractivityManager()
        result = manager.setup_map_interactivity(test_map)
        assert result is manager
        html = test_map._repr_html_()
        assert 'showNotification' in html

    def test_custom_server_url_in_output(self):
        from visual.interactivity import InteractivityManager
        test_map = folium.Map(location=[51.5074, -0.1278])
        manager = InteractivityManager(server_url='https://api.example.com')
        manager.setup_map_interactivity(test_map)
        html = test_map._repr_html_()
        # get_js() intentionally uses empty URL for relative paths (works on any port).
        # In iframe srcdoc, quotes are HTML-encoded as &quot;
        assert 'BACKEND_CONFIG' in html
        assert '&quot;url&quot;: &quot;&quot;' in html
        # The server_url is stored on the object for statistics/config
        assert manager.backend.server_url == 'https://api.example.com'


class TestUtilityIntegration:
    """Utility modules must handle typical inputs correctly."""

    def test_format_currency_gbp(self):
        from visual.utils import DataFormatter
        result = DataFormatter.format_currency(750000)
        assert isinstance(result, str)
        assert '750' in result

    def test_risk_assessor_levels(self):
        from visual.utils import RiskAssessor
        low = RiskAssessor.assess_flood_risk_level(0.05)
        high = RiskAssessor.assess_flood_risk_level(2.5)
        assert isinstance(low, str)
        assert isinstance(high, str)
        assert low != high

    def test_color_schemes_vary_by_risk(self):
        from visual.utils import ColorSchemes
        high_color = ColorSchemes.get_flood_risk_color('High')
        low_color = ColorSchemes.get_flood_risk_color('Low')
        assert high_color != low_color

    def test_data_formatter_percentage(self):
        from visual.utils import DataFormatter
        result = DataFormatter.format_percentage(0.0525)
        assert isinstance(result, str)
        assert '%' in result or '5' in result
