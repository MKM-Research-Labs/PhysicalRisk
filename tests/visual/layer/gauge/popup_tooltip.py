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

"""
Tests for GaugeLayer._create_gauge_popup and _create_gauge_tooltip.
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
                    "GaugeLatitude": lat, "GaugeLongitude": lon,
                    "GaugeOwner": "EA", "GaugeType": "Pressure",
                    "OperationalStatus": status, "DataSourceType": "API",
                    "InstallationDate": "2010-01-01",
                    "CertificationStatus": "Certified", "GroundLevelMeters": 3.0,
                },
                "Measurements": {
                    "MeasurementFrequency": "15min",
                    "MeasurementMethod": "Pressure", "DataTransmission": "GSM",
                },
            },
            "SensorStats": {
                "HistoricalHighLevel": 5.5, "HistoricalHighDate": "2014-02-07",
                "LastDateLevelExceedLevel3": "2020-01-01", "FrequencyExceedLevel3": 3,
            },
            "FloodStage": {"UK": {
                "FloodAlert": 4.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.0,
            }},
        }
    }


def _layer_with_gauge(gauge_id="GAUGE-001", name="Test Gauge"):
    layer = GaugeLayer()
    layer._gauge_hazard = {}
    layer._num_storms = 10000
    gauge_info = layer._extract_gauges({"items": [_make_gauge_item(gauge_id, name)]})[0]
    return layer, gauge_info


# ===========================================================================
# _create_gauge_popup
# ===========================================================================

class TestCreateGaugePopup:

    def test_returns_html_string(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "Test Location")
        assert isinstance(html, str)
        assert "GAUGE-001" in html

    def test_popup_contains_gauge_name(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "West London area")
        assert "Test Gauge" in html

    def test_popup_with_empty_gauge_name_fallback(self):
        """Empty gauge_name → header shows 'Flood Gauge'."""
        layer, gauge_info = _layer_with_gauge(name="")
        html = layer._create_gauge_popup(gauge_info, {}, "East London area")
        assert "Flood Gauge" in html

    def test_popup_contains_flood_thresholds(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "Central London")
        assert "Alert Level" in html
        assert "Warning Level" in html
        assert "Severe Warning" in html

    def test_popup_contains_location_desc(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "West London area")
        assert "West London area" in html

    def test_popup_contains_coordinates(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "Central London")
        assert "51.5" in html

    def test_popup_contains_equipment_section(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "Central London")
        assert "Equipment Details" in html
        assert "EA" in html  # GaugeOwner

    def test_popup_contains_historical_high(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "East London area")
        assert "Historical High" in html
        assert "2014-02-07" in html

    def test_popup_contains_sensor_section(self):
        layer, gauge_info = _layer_with_gauge()
        html = layer._create_gauge_popup(gauge_info, {}, "Central London")
        assert "Sensor" in html
        assert "Ground Elevation" in html


# ===========================================================================
# _create_gauge_tooltip
# ===========================================================================

class TestCreateGaugeTooltip:

    def test_tooltip_contains_gauge_id(self):
        layer, gauge_info = _layer_with_gauge("GAUGE-001")
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "GAUGE-001" in tip

    def test_tooltip_contains_flood_count(self):
        layer, gauge_info = _layer_with_gauge()
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "Floods:" in tip

    def test_tooltip_contains_frequency_label(self):
        layer, gauge_info = _layer_with_gauge()
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "Low" in tip or "Medium" in tip or "High" in tip

    def test_tooltip_with_empty_name_uses_gauge_id(self):
        """Empty gauge_name → label = gauge_id."""
        layer, gauge_info = _layer_with_gauge("GAUGE-NO-NAME", name="")
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "GAUGE-NO-NAME" in tip

    def test_tooltip_with_name_uses_name(self):
        """Non-empty gauge_name used as primary label."""
        layer, gauge_info = _layer_with_gauge("GAUGE-001", name="Chelsea Gauge")
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "Chelsea Gauge" in tip

    def test_tooltip_contains_alert_level(self):
        layer, gauge_info = _layer_with_gauge()
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "Alert" in tip

    def test_tooltip_with_high_flood_count(self):
        """High flood count shows 'High' label."""
        layer = GaugeLayer()
        layer._gauge_hazard = {"GAUGE-001": {"annual_hazard_rate_warning": 0.03}}
        layer._num_storms = 10000
        gauge_info = layer._extract_gauges({"items": [_make_gauge_item("GAUGE-001")]})[0]
        tip = layer._create_gauge_tooltip(gauge_info)
        assert "High" in tip
