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
Tests for GaugeLayer.__init__ attributes and _extract_gauges.
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


# ===========================================================================
# __init__
# ===========================================================================

class TestGaugeLayerInit:

    def test_layer_name(self):
        assert GaugeLayer().layer_name == "Flood Gauges"

    def test_show_status_colors_default(self):
        assert GaugeLayer().show_status_colors is True

    def test_show_flood_thresholds_default(self):
        assert GaugeLayer().show_flood_thresholds is True

    def test_status_icons_present(self):
        layer = GaugeLayer()
        for status in ["Fully operational", "Maintenance required",
                       "Temporarily offline", "Decommissioned", "Unknown"]:
            assert status in layer.status_icons

    def test_status_icons_are_folium_icons(self):
        layer = GaugeLayer()
        for icon in layer.status_icons.values():
            assert isinstance(icon, folium.Icon)


# ===========================================================================
# _extract_gauges — key format variants
# ===========================================================================

class TestExtractGaugesKeyFormats:

    def test_items_key(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item()]})
        assert len(result) == 1

    def test_flood_gauges_key(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"flood_gauges": [_make_gauge_item()]})
        assert len(result) == 1

    def test_floodGauges_camel_key(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"floodGauges": [_make_gauge_item()]})
        assert len(result) == 1

    def test_empty_data_returns_empty_list(self):
        layer = GaugeLayer()
        assert layer._extract_gauges({}) == []
        assert layer._extract_gauges({"items": []}) == []

    def test_malformed_gauge_skipped_via_exception(self, caplog):
        """Lines 102-104: a record that raises during processing is logged
        and skipped rather than aborting the whole extraction."""
        import logging

        good = _make_gauge_item(gauge_id="GAUGE-good")
        bad = _make_gauge_item(gauge_id="GAUGE-bad")
        # Force a ValueError on float(lat)
        bad["FloodGauge"]["SensorDetails"]["GaugeInformation"]["GaugeLatitude"] = "not-a-number"

        layer = GaugeLayer()
        with caplog.at_level(logging.WARNING, logger="visual.layer.gauge_layer.extract"):
            result = layer._extract_gauges({"items": [good, bad]})

        # Only the well-formed record made it through
        assert len(result) == 1
        assert result[0]["gauge_id"] == "GAUGE-good"
        assert any("Error extracting gauge data" in r.message for r in caplog.records)


# ===========================================================================
# _extract_gauges — field extraction
# ===========================================================================

class TestExtractGaugesFields:

    def test_extracts_gauge_id(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item(gauge_id="GAUGE-007")]})
        assert result[0]["gauge_id"] == "GAUGE-007"

    def test_extracts_lat_lon_as_floats(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item(lat=51.5, lon=-0.1)]})
        assert result[0]["lat"] == pytest.approx(51.5)
        assert result[0]["lon"] == pytest.approx(-0.1)

    def test_extracts_operational_status(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item(status="Maintenance required")]})
        assert result[0]["operational_status"] == "Maintenance required"

    def test_extracts_flood_thresholds(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item()]})
        assert result[0]["flood_alert"] == pytest.approx(4.0)
        assert result[0]["flood_warning"] == pytest.approx(4.5)
        assert result[0]["severe_warning"] == pytest.approx(5.0)

    def test_extracts_historical_high(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item()]})
        assert result[0]["historical_high"] == pytest.approx(5.5)

    def test_extracts_sensor_stats(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item()]})
        assert result[0]["historical_high_date"] == "2014-02-07"
        assert result[0]["frequency_exceed_level3"] == 3

    def test_extracts_measurement_fields(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item()]})
        assert result[0]["measurement_frequency"] == "15min"
        assert result[0]["data_transmission"] == "GSM"

    def test_extracts_ground_elevation(self):
        layer = GaugeLayer()
        result = layer._extract_gauges({"items": [_make_gauge_item()]})
        assert result[0]["ground_elevation"] == pytest.approx(3.0)

    def test_multiple_gauges(self):
        layer = GaugeLayer()
        data = {"items": [_make_gauge_item("G1", lat=51.4, lon=-0.2),
                          _make_gauge_item("G2", lat=51.5, lon=-0.1)]}
        result = layer._extract_gauges(data)
        assert len(result) == 2


# ===========================================================================
# _extract_gauges — filtering and error handling
# ===========================================================================

class TestExtractGaugesFiltering:

    def test_skips_gauge_with_missing_lat(self):
        layer = GaugeLayer()
        item = _make_gauge_item()
        item["FloodGauge"]["SensorDetails"]["GaugeInformation"]["GaugeLatitude"] = None
        assert layer._extract_gauges({"items": [item]}) == []

    def test_skips_gauge_with_missing_lon(self):
        layer = GaugeLayer()
        item = _make_gauge_item()
        item["FloodGauge"]["SensorDetails"]["GaugeInformation"]["GaugeLongitude"] = None
        assert layer._extract_gauges({"items": [item]}) == []

    def test_bad_gauge_skipped_gracefully(self):
        """Completely malformed entry skipped; valid entry kept."""
        layer = GaugeLayer()
        data = {"items": [{"broken": "data"}, _make_gauge_item()]}
        result = layer._extract_gauges(data)
        assert len(result) == 1

    def test_defaults_for_missing_header_fields(self):
        """Missing GaugeID defaults to 'Unknown'."""
        layer = GaugeLayer()
        item = _make_gauge_item()
        del item["FloodGauge"]["Header"]["GaugeID"]
        result = layer._extract_gauges({"items": [item]})
        assert result[0]["gauge_id"] == "Unknown"
