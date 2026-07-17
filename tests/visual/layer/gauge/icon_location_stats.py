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
Tests for GaugeLayer flood count, icon, location description,
configure, and get_gauge_statistics.
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
                    "OperationalStatus": status,
                    "DataSourceType": "API", "InstallationDate": "2010-01-01",
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


def _layer():
    layer = GaugeLayer()
    layer._gauge_hazard = {}
    layer._num_storms = 10000
    return layer


# ===========================================================================
# _get_gauge_flood_count
# ===========================================================================

class TestGetGaugeFloodCount:

    def test_returns_zero_with_no_hazard(self):
        layer = _layer()
        assert layer._get_gauge_flood_count("GAUGE-999") == 0

    def test_returns_calculated_count(self):
        layer = _layer()
        layer._gauge_hazard = {"GAUGE-001": {
            "annual_hazard_rate_warning": 0.03, "num_storms_simulated": 10000
        }}
        assert layer._get_gauge_flood_count("GAUGE-001") == 300

    def test_uses_default_num_storms_when_missing(self):
        layer = _layer()
        layer._gauge_hazard = {"GAUGE-001": {"annual_hazard_rate_warning": 0.025}}
        layer._num_storms = 8000
        assert layer._get_gauge_flood_count("GAUGE-001") == 200

    def test_zero_rate_gives_zero_count(self):
        layer = _layer()
        layer._gauge_hazard = {"GAUGE-001": {
            "annual_hazard_rate_warning": 0.0, "num_storms_simulated": 10000
        }}
        assert layer._get_gauge_flood_count("GAUGE-001") == 0


# ===========================================================================
# _get_gauge_flood_frequency_label
# ===========================================================================

class TestGetGaugeFloodFrequencyLabel:

    def test_high_label(self):
        """flood_count > 250 → High."""
        assert GaugeLayer._get_gauge_flood_frequency_label(251) == "High"
        assert GaugeLayer._get_gauge_flood_frequency_label(1000) == "High"

    def test_medium_label(self):
        """220 <= flood_count <= 250 → Medium."""
        assert GaugeLayer._get_gauge_flood_frequency_label(235) == "Medium"
        assert GaugeLayer._get_gauge_flood_frequency_label(220) == "Medium"
        assert GaugeLayer._get_gauge_flood_frequency_label(250) == "Medium"

    def test_low_label(self):
        """flood_count < 220 → Low."""
        assert GaugeLayer._get_gauge_flood_frequency_label(100) == "Low"
        assert GaugeLayer._get_gauge_flood_frequency_label(0) == "Low"
        assert GaugeLayer._get_gauge_flood_frequency_label(219) == "Low"


# ===========================================================================
# _get_gauge_icon
# ===========================================================================

class TestGetGaugeIcon:

    def test_returns_folium_icon(self):
        layer = _layer()
        icon = layer._get_gauge_icon({"gauge_id": "GAUGE-001"}, {})
        assert isinstance(icon, folium.Icon)

    def test_blue_for_fully_operational(self):
        """Fully operational → blue icon."""
        layer = _layer()
        icon = layer._get_gauge_icon(
            {"gauge_id": "GAUGE-001", "operational_status": "Fully operational"}, {})
        assert icon.options["marker_color"] == "blue"

    def test_red_for_temporarily_offline(self):
        """Temporarily offline → red icon."""
        layer = _layer()
        icon = layer._get_gauge_icon(
            {"gauge_id": "GAUGE-001", "operational_status": "Temporarily offline"}, {})
        assert icon.options["marker_color"] == "red"

    def test_orange_for_maintenance_required(self):
        """Maintenance required → orange icon."""
        layer = _layer()
        icon = layer._get_gauge_icon(
            {"gauge_id": "GAUGE-001", "operational_status": "Maintenance required"}, {})
        assert icon.options["marker_color"] == "orange"

    def test_gray_for_decommissioned(self):
        """Decommissioned → gray icon."""
        layer = _layer()
        icon = layer._get_gauge_icon(
            {"gauge_id": "GAUGE-001", "operational_status": "Decommissioned"}, {})
        assert icon.options["marker_color"] == "gray"

    def test_blue_default_for_unknown_status(self):
        """Unknown or missing status → blue (default)."""
        layer = _layer()
        icon = layer._get_gauge_icon({"gauge_id": "GAUGE-001"}, {})
        assert icon.options["marker_color"] == "blue"

    def test_icon_uses_tint_fa_prefix(self):
        layer = _layer()
        icon = layer._get_gauge_icon({"gauge_id": "GAUGE-001"}, {})
        assert icon.options["icon"] == "tint"
        assert icon.options["prefix"] == "fa"


# ===========================================================================
# _get_location_description
# ===========================================================================

class TestGetLocationDescription:
    """Location description follows the active catchment's own longitude span,
    not a hardcoded London region."""

    def _bounds(self):
        from config.visual import get_catchment_bounds
        min_lon, min_lat, max_lon, max_lat = get_catchment_bounds()
        return min_lon, max_lon, (min_lat + max_lat) / 2.0

    def test_western_part(self):
        min_lon, max_lon, lat = self._bounds()
        lon = min_lon + 0.1 * (max_lon - min_lon)
        assert GaugeLayer()._get_location_description(lat, lon) == "Western part of catchment"

    def test_central_part(self):
        min_lon, max_lon, lat = self._bounds()
        lon = min_lon + 0.5 * (max_lon - min_lon)
        assert GaugeLayer()._get_location_description(lat, lon) == "Central part of catchment"

    def test_eastern_part(self):
        min_lon, max_lon, lat = self._bounds()
        lon = min_lon + 0.9 * (max_lon - min_lon)
        assert GaugeLayer()._get_location_description(lat, lon) == "Eastern part of catchment"


# ===========================================================================
# configure
# ===========================================================================

class TestConfigure:

    def test_configure_sets_flags(self):
        layer = GaugeLayer()
        layer.configure(show_status_colors=False, show_flood_thresholds=False)
        assert layer.show_status_colors is False
        assert layer.show_flood_thresholds is False

    def test_configure_defaults_true(self):
        layer = GaugeLayer()
        layer.configure()
        assert layer.show_status_colors is True
        assert layer.show_flood_thresholds is True

    def test_configure_partial_update(self):
        layer = GaugeLayer()
        layer.configure(show_status_colors=False)
        assert layer.show_status_colors is False
        assert layer.show_flood_thresholds is True


# ===========================================================================
# get_gauge_statistics
# ===========================================================================

class TestGetGaugeStatistics:

    def _gauges(self):
        layer = _layer()
        return layer._extract_gauges({"items": [
            _make_gauge_item("G1", status="Fully operational"),
            _make_gauge_item("G2", status="Fully operational"),
            _make_gauge_item("G3", status="Maintenance required"),
        ]})

    def test_empty_gauges_returns_empty_dict(self):
        assert GaugeLayer().get_gauge_statistics([]) == {}

    def test_total_count(self):
        layer = _layer()
        stats = layer.get_gauge_statistics(self._gauges())
        assert stats["total_gauges"] == 3

    def test_status_distribution(self):
        layer = _layer()
        stats = layer.get_gauge_statistics(self._gauges())
        assert stats["status_distribution"]["Fully operational"] == 2
        assert stats["status_distribution"]["Maintenance required"] == 1

    def test_type_distribution(self):
        layer = _layer()
        stats = layer.get_gauge_statistics(self._gauges())
        assert "Pressure" in stats["type_distribution"]
        assert stats["type_distribution"]["Pressure"] == 3

    def test_owner_distribution(self):
        layer = _layer()
        stats = layer.get_gauge_statistics(self._gauges())
        assert "EA" in stats["owner_distribution"]
        assert stats["owner_distribution"]["EA"] == 3

    def test_operational_percentage(self):
        layer = _layer()
        stats = layer.get_gauge_statistics(self._gauges())
        assert stats["operational_percentage"] == pytest.approx(200 / 3)

    def test_all_operational_100_percent(self):
        layer = _layer()
        gauges = layer._extract_gauges({"items": [
            _make_gauge_item("G1"), _make_gauge_item("G2"),
        ]})
        stats = layer.get_gauge_statistics(gauges)
        assert stats["operational_percentage"] == pytest.approx(100.0)
