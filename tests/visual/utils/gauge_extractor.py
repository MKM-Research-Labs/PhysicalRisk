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
Tests for visual.utils.data_extractors.gauge_extractor.

Covers: extract_gauge_info and extract_flood_risk_data.
"""

import pytest

from visual.utils.data_extractors.gauge_extractor import (
    extract_gauge_info,
    extract_flood_risk_data,
)


# ===========================================================================
# extract_gauge_info
# ===========================================================================

def _make_gauge(gauge_id="GAUGE-001", lat=51.5, lon=-0.1, name="Test Gauge",
                operational_status="Fully operational"):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id, "GaugeName": name},
            "SensorDetails": {
                "GaugeInformation": {
                    "GaugeLatitude": lat,
                    "GaugeLongitude": lon,
                    "GaugeOwner": "EA",
                    "GaugeType": "Pressure",
                    "OperationalStatus": operational_status,
                    "DataSourceType": "API",
                    "InstallationDate": "2010-01-01",
                    "CertificationStatus": "Certified",
                },
                "Measurements": {
                    "MeasurementFrequency": "15min",
                    "MeasurementMethod": "Pressure",
                    "DataTransmission": "GSM",
                }
            },
            "SensorStats": {"HistoricalHighLevel": 5.5},
            "FloodStage": {
                "UK": {
                    "FloodAlert": 4.0,
                    "FloodWarning": 4.5,
                    "SevereFloodWarning": 5.0,
                }
            },
        }
    }


class TestExtractGaugeInfo:

    def test_returns_dict_for_valid_gauge(self):
        result = extract_gauge_info(_make_gauge())
        assert isinstance(result, dict)

    def test_extracts_gauge_id(self):
        result = extract_gauge_info(_make_gauge(gauge_id="GAUGE-007"))
        assert result["gauge_id"] == "GAUGE-007"

    def test_extracts_coordinates(self):
        result = extract_gauge_info(_make_gauge(lat=51.5, lon=-0.1))
        assert result["coordinates"]["latitude"] == pytest.approx(51.5)
        assert result["coordinates"]["longitude"] == pytest.approx(-0.1)

    def test_extracts_operational_status(self):
        result = extract_gauge_info(_make_gauge(operational_status="Maintenance required"))
        assert result["operational_status"] == "Maintenance required"

    def test_extracts_flood_stage(self):
        result = extract_gauge_info(_make_gauge())
        assert result["flood_stage"]["FloodAlert"] == pytest.approx(4.0)

    def test_extracts_sensor_stats(self):
        result = extract_gauge_info(_make_gauge())
        assert result["sensor_stats"]["HistoricalHighLevel"] == pytest.approx(5.5)

    def test_missing_lat_returns_none(self):
        gauge = _make_gauge()
        gauge["FloodGauge"]["SensorDetails"]["GaugeInformation"]["GaugeLatitude"] = None
        assert extract_gauge_info(gauge) is None

    def test_missing_lon_returns_none(self):
        gauge = _make_gauge()
        gauge["FloodGauge"]["SensorDetails"]["GaugeInformation"]["GaugeLongitude"] = None
        assert extract_gauge_info(gauge) is None

    def test_no_nested_floodgauge_key(self):
        # Flat dict (no 'FloodGauge' wrapper) — should still work
        flat = {
            "Header": {"GaugeID": "G-FLAT"},
            "SensorDetails": {
                "GaugeInformation": {"GaugeLatitude": 52.0, "GaugeLongitude": 0.5},
                "Measurements": {},
            },
            "SensorStats": {},
            "FloodStage": {},
        }
        result = extract_gauge_info(flat)
        assert result is not None
        assert result["gauge_id"] == "G-FLAT"

    def test_original_data_preserved(self):
        result = extract_gauge_info(_make_gauge())
        assert "original_data" in result

    def test_measurement_fields_extracted(self):
        result = extract_gauge_info(_make_gauge())
        assert result["measurement_frequency"] == "15min"
        assert result["measurement_method"] == "Pressure"
        assert result["data_transmission"] == "GSM"


# ===========================================================================
# extract_flood_risk_data
# ===========================================================================

class TestExtractFloodRiskData:

    def _make_report(self):
        return {
            "gauge_data": {
                "GAUGE-001": {
                    "gauge_name": "Thames at Chelsea",
                    "elevation": 3.5,
                    "max_level": 5.5,
                    "alert_level": 4.0,
                    "warning_level": 4.5,
                    "severe_level": 5.0,
                    "max_gauge_reading": 5.5,
                }
            },
            "property_risk": {
                "PROP-001": {
                    "property_id": "PROP-001",
                    "property_elevation": 5.0,
                    "nearest_gauge": "Thames at Chelsea",
                    "nearest_gauge_id": "GAUGE-001",
                    "distance_to_gauge": 0.5,
                    "risk_level": "High",
                    "flood_depth": 0.3,
                    "risk_value": 0.08,
                    "property_value": 400_000,
                    "value_at_risk": 32_000,
                }
            },
            "mortgage_risk": {
                "MORT-001": {
                    "MortgageID": "MORT-001",
                    "PropertyID": "PROP-001",
                    "mortgage_value": 250_000,
                }
            },
        }

    def test_returns_dict_with_required_keys(self):
        result = extract_flood_risk_data(self._make_report())
        assert "gauge_flood_info" in result
        assert "property_flood_info" in result

    def test_extracts_gauge_data(self):
        result = extract_flood_risk_data(self._make_report())
        assert "GAUGE-001" in result["gauge_flood_info"]
        assert result["gauge_flood_info"]["GAUGE-001"]["gauge_name"] == "Thames at Chelsea"

    def test_extracts_property_data(self):
        result = extract_flood_risk_data(self._make_report())
        assert "PROP-001" in result["property_flood_info"]
        assert result["property_flood_info"]["PROP-001"]["risk_level"] == "High"

    def test_empty_report_returns_empty_structure(self):
        result = extract_flood_risk_data({})
        assert result["gauge_flood_info"] == {}
        assert result["property_flood_info"] == {}
