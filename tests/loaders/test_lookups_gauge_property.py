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

"""Tests for build_gauge_flood_info, build_property_flood_info, _classify_property_risk."""

import pytest

from loaders.lookups import (
    build_gauge_flood_info,
    build_property_flood_info,
    _classify_property_risk,
)


# ===========================================================================
# build_gauge_flood_info
# ===========================================================================

class TestBuildGaugeFloodInfo:

    def test_both_none_returns_empty(self):
        assert build_gauge_flood_info(None, None) == {}

    def test_hazard_curves_only(self):
        flood_risk_data = {
            "hazard_curves": {
                "GAUGE-001": {
                    "gauge_name": "Thames at Chelsea",
                    "elevation_m": 3.5,
                    "flood_alert_m": 4.0,
                    "flood_warning_m": 4.5,
                    "severe_flood_warning_m": 5.0,
                    "annual_flood_prob_alert": 0.2,
                    "annual_flood_prob_warning": 0.1,
                    "annual_flood_prob_severe": 0.05,
                    "annual_hazard_rate_alert": 0.22,
                    "annual_hazard_rate_warning": 0.11,
                    "annual_hazard_rate_severe": 0.055,
                }
            }
        }
        result = build_gauge_flood_info(None, flood_risk_data)
        assert "GAUGE-001" in result
        assert result["GAUGE-001"]["gauge_name"] == "Thames at Chelsea"
        assert result["GAUGE-001"]["alert_level"] == 4.0
        assert result["GAUGE-001"]["annual_flood_prob_warning"] == pytest.approx(0.1)

    def test_gauge_data_supplements_missing_fields(self):
        gauge_data = {
            "items": [{
                "FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-002", "GaugeName": "My Gauge"},
                    "FloodStages": {
                        "FloodAlert": 3.0,
                        "FloodWarning": 3.5,
                        "SevereFloodWarning": 4.0,
                    },
                    "Location": {"GaugeElevation": 2.0},
                    "SensorStats": {"HistoricalHighLevel": 5.5},
                }
            }]
        }
        result = build_gauge_flood_info(gauge_data, None)
        assert "GAUGE-002" in result
        assert result["GAUGE-002"]["gauge_name"] == "My Gauge"
        assert result["GAUGE-002"]["alert_level"] == 3.0
        assert result["GAUGE-002"]["max_level"] == 5.5

    def test_hazard_data_takes_precedence(self):
        # Gauge in both hazard_curves and gauge_data — hazard_curves wins
        flood_risk_data = {
            "hazard_curves": {
                "GAUGE-003": {"gauge_name": "From HC", "elevation_m": 10.0}
            }
        }
        gauge_data = {
            "items": [{
                "FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-003", "GaugeName": "From Gauge"},
                    "FloodStages": {},
                    "Location": {},
                    "SensorStats": {},
                }
            }]
        }
        result = build_gauge_flood_info(gauge_data, flood_risk_data)
        assert result["GAUGE-003"]["gauge_name"] == "From HC"

    def test_gauge_without_id_skipped(self):
        gauge_data = {
            "items": [{
                "FloodGauge": {
                    "Header": {},  # No GaugeID
                    "FloodStages": {},
                    "Location": {},
                    "SensorStats": {},
                }
            }]
        }
        result = build_gauge_flood_info(gauge_data, None)
        assert result == {}


# ===========================================================================
# build_property_flood_info
# ===========================================================================

class TestBuildPropertyFloodInfo:

    def test_all_none_returns_empty(self):
        assert build_property_flood_info(None, None, None) == {}

    def test_from_property_hazard_data(self):
        phc = {
            "property_hazard_curves": {
                "PROP-001": {
                    "elevation_m": 5.0,
                    "floor_level_m": 5.2,
                    "flood_count": 3,
                    "location": {"lat": 51.5, "lon": -0.1},
                    "depth_thresholds": {
                        "any_flood": {"annual_probability": 0.05},
                        "moderate": {"annual_probability": 0.02},
                        "severe": {"annual_probability": 0.005},
                    }
                }
            }
        }
        result = build_property_flood_info(None, None, phc)
        assert "PROP-001" in result
        assert result["PROP-001"]["annual_flood_prob"] == pytest.approx(0.05)
        assert result["PROP-001"]["risk_level"] == "High"
        assert result["PROP-001"]["lat"] == 51.5

    def test_from_property_data_when_not_in_phc(self):
        property_data = {
            "items": [{
                "PropertyHeader": {
                    "Header": {"PropertyID": "PROP-002"},
                    "RiskAssessment": {
                        "GroundLevelMeters": 4.0,
                        "EAFloodZone": "Zone 2",
                        "OverallFloodRisk": "Medium",
                    },
                    "Location": {"LatitudeDegrees": 51.4, "LongitudeDegrees": -0.2},
                }
            }]
        }
        result = build_property_flood_info(property_data, None, None)
        assert "PROP-002" in result
        assert result["PROP-002"]["flood_zone"] == "Zone 2"
        assert result["PROP-002"]["risk_level"] == "Medium"

    def test_phc_takes_precedence_over_property_data(self):
        phc = {
            "property_hazard_curves": {
                "PROP-003": {
                    "elevation_m": 1.0,
                    "floor_level_m": 1.5,
                    "flood_count": 1,
                    "location": {},
                    "depth_thresholds": {
                        "any_flood": {"annual_probability": 0.01},
                        "moderate": {"annual_probability": 0.0},
                        "severe": {"annual_probability": 0.0},
                    }
                }
            }
        }
        property_data = {
            "items": [{
                "PropertyHeader": {
                    "Header": {"PropertyID": "PROP-003"},
                    "RiskAssessment": {"OverallFloodRisk": "High"},
                    "Location": {},
                }
            }]
        }
        result = build_property_flood_info(property_data, None, phc)
        # Should use PHC data (risk_level from _classify_property_risk, not "High")
        assert result["PROP-003"]["annual_flood_prob"] == pytest.approx(0.01)


# ===========================================================================
# _classify_property_risk
# ===========================================================================

class TestClassifyPropertyRisk:

    def test_zero_is_negligible(self):
        assert _classify_property_risk(0.0) == "Negligible"

    def test_tiny_prob_is_low(self):
        assert _classify_property_risk(0.005) == "Low"

    def test_medium_threshold(self):
        assert _classify_property_risk(0.01) == "Medium"

    def test_high_threshold(self):
        assert _classify_property_risk(0.03) == "High"

    def test_above_high_threshold_is_high(self):
        assert _classify_property_risk(0.5) == "High"

    def test_just_below_medium_is_low(self):
        assert _classify_property_risk(0.009) == "Low"
