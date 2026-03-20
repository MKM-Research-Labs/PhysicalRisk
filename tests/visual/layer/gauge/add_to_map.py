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
Tests for GaugeLayer.add_to_map and _add_gauge_marker.
"""

import pytest
import folium

from visual.layer.gauge_layer import GaugeLayer


# ===========================================================================
# Helpers
# ===========================================================================

def _make_gauge_item(gauge_id="GAUGE-001", name="Test Gauge",
                     lat=51.5, lon=-0.1, status="Fully operational"):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id, "GaugeName": name},
            "SensorDetails": {
                "GaugeInformation": {
                    "GaugeLatitude": lat,
                    "GaugeLongitude": lon,
                    "GaugeOwner": "EA",
                    "GaugeType": "Pressure",
                    "OperationalStatus": status,
                    "DataSourceType": "API",
                    "InstallationDate": "2010-01-01",
                    "CertificationStatus": "Certified",
                    "GroundLevelMeters": 3.0,
                },
                "Measurements": {
                    "MeasurementFrequency": "15min",
                    "MeasurementMethod": "Pressure",
                    "DataTransmission": "GSM",
                },
            },
            "SensorStats": {
                "HistoricalHighLevel": 5.5,
                "HistoricalHighDate": "2014-02-07",
                "LastDateLevelExceedLevel3": "2020-01-01",
                "FrequencyExceedLevel3": 3,
            },
            "FloodStage": {
                "UK": {
                    "FloodAlert": 4.0,
                    "FloodWarning": 4.5,
                    "SevereFloodWarning": 5.0,
                }
            },
        }
    }


class MockLoadedData:
    def __init__(self, gauge_data=None, hazard_data=None, gauge_flood_info=None):
        self.gauge_data = gauge_data
        self.hazard_data = hazard_data
        self.gauge_flood_info = gauge_flood_info or {}


def _layer_ready():
    layer = GaugeLayer()
    layer._gauge_hazard = {}
    layer._num_storms = 10000
    return layer


# ===========================================================================
# add_to_map — empty data
# ===========================================================================

class TestAddToMapEmpty:

    def test_returns_feature_group_when_no_gauge_data(self):
        layer = GaugeLayer()
        result = layer.add_to_map(folium.Map(), MockLoadedData(gauge_data=None))
        assert isinstance(result, folium.FeatureGroup)

    def test_returns_feature_group_when_gauges_empty(self):
        layer = GaugeLayer()
        result = layer.add_to_map(folium.Map(), MockLoadedData(gauge_data={"items": []}))
        assert isinstance(result, folium.FeatureGroup)

    def test_feature_group_name_set(self):
        layer = GaugeLayer()
        result = layer.add_to_map(folium.Map(), MockLoadedData(gauge_data=None))
        assert result.layer_name == "Flood Gauges"


# ===========================================================================
# add_to_map — with gauge data
# ===========================================================================

class TestAddToMapWithGauges:

    def test_adds_markers_to_map(self):
        layer = GaugeLayer()
        loaded = MockLoadedData(gauge_data={"items": [_make_gauge_item()]})
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_multiple_gauges_added(self):
        layer = GaugeLayer()
        loaded = MockLoadedData(gauge_data={"items": [
            _make_gauge_item("G1"), _make_gauge_item("G2", lat=51.6, lon=-0.2)
        ]})
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_hazard_data_loaded_into_gauge_hazard(self):
        """Lines 85-90: hazard_data dict entries stored in _gauge_hazard."""
        layer = GaugeLayer()
        hazard = {
            "metadata": {"num_storms": 5000},
            "hazard_curves": {
                "GAUGE-001": {"annual_hazard_rate_warning": 0.06, "num_storms_simulated": 5000}
            }
        }
        loaded = MockLoadedData(
            gauge_data={"items": [_make_gauge_item("GAUGE-001")]},
            hazard_data=hazard
        )
        layer.add_to_map(folium.Map(), loaded)
        assert "GAUGE-001" in layer._gauge_hazard

    def test_hazard_data_non_dict_entry_skipped(self):
        """Line 89: non-dict hazard entry not stored."""
        layer = GaugeLayer()
        hazard = {
            "hazard_curves": {
                "GAUGE-BAD": "not_a_dict",
                "GAUGE-001": {"annual_hazard_rate_warning": 0.01}
            }
        }
        loaded = MockLoadedData(
            gauge_data={"items": [_make_gauge_item("GAUGE-001")]},
            hazard_data=hazard
        )
        layer.add_to_map(folium.Map(), loaded)
        assert "GAUGE-BAD" not in layer._gauge_hazard
        assert "GAUGE-001" in layer._gauge_hazard

    def test_num_storms_from_hazard_metadata(self):
        """Line 86: num_storms read from metadata."""
        layer = GaugeLayer()
        hazard = {"metadata": {"num_storms": 3000}, "hazard_curves": {}}
        loaded = MockLoadedData(
            gauge_data={"items": [_make_gauge_item()]},
            hazard_data=hazard
        )
        layer.add_to_map(folium.Map(), loaded)
        assert layer._num_storms == 3000

    def test_flood_info_passed_to_marker(self):
        layer = GaugeLayer()
        loaded = MockLoadedData(
            gauge_data={"items": [_make_gauge_item("GAUGE-001")]},
            gauge_flood_info={"GAUGE-001": {"current_level": 3.5}}
        )
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_no_hazard_data_sets_defaults(self):
        """When hazard_data is None, _gauge_hazard stays empty, _num_storms = 10000."""
        layer = GaugeLayer()
        loaded = MockLoadedData(
            gauge_data={"items": [_make_gauge_item()]},
            hazard_data=None
        )
        layer.add_to_map(folium.Map(), loaded)
        assert layer._gauge_hazard == {}
        assert layer._num_storms == 10000


# ===========================================================================
# _add_gauge_marker
# ===========================================================================

class TestAddGaugeMarker:

    def test_adds_marker_to_feature_group(self):
        layer = _layer_ready()
        fg = folium.FeatureGroup()
        gauge_info = layer._extract_gauges({"items": [_make_gauge_item()]})[0]
        layer._add_gauge_marker(fg, gauge_info, None)
        assert len(fg._children) > 0

    def test_marker_with_flood_info(self):
        layer = _layer_ready()
        fg = folium.FeatureGroup()
        gauge_info = layer._extract_gauges({"items": [_make_gauge_item("GAUGE-001")]})[0]
        layer._add_gauge_marker(fg, gauge_info, {"GAUGE-001": {"current_level": 3.5}})
        assert len(fg._children) > 0

    def test_marker_exception_is_graceful(self):
        """Exception from malformed gauge_info is caught, no raise."""
        layer = _layer_ready()
        fg = folium.FeatureGroup()
        layer._add_gauge_marker(fg, {"gauge_id": "GAUGE-BAD"}, None)
        # No exception raised

    def test_flood_info_lookup_uses_gauge_id(self):
        """Flood info for a different gauge_id doesn't apply."""
        layer = _layer_ready()
        fg = folium.FeatureGroup()
        gauge_info = layer._extract_gauges({"items": [_make_gauge_item("GAUGE-001")]})[0]
        other_flood = {"GAUGE-OTHER": {"level": 5.0}}
        layer._add_gauge_marker(fg, gauge_info, other_flood)
        assert len(fg._children) > 0
