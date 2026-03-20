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

"""Extra tests for gauge_generator.py covering _find_gauge_by_id and auto_open path."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from reports.gauge.gauge_generator import _find_gauge_by_id, generate_gauge_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_gauge_data() -> Dict[str, Any]:
    """Gauge data in the CDM format expected by the report generator."""
    return {
        "FloodGauge": {
            "Header": {
                "GaugeID": "GAUGE-test0001",
                "CatchmentID": "thames",
                "GaugeName": "Thames Test Gauge"
            },
            "SensorStats": {
                "HistoricalHighLevel": 6.85,
                "HistoricalHighDate": "2024-01-15",
                "LastDateLevelExceedLevel3": "2023-11-10",
                "FrequencyExceedLevel3": 2
            },
            "SensorDetails": {
                "GaugeInformation": {
                    "DataSourceType": "SensorGauge",
                    "GaugeOwner": "Environment Agency",
                    "GaugeType": "Pressure transducer",
                    "ManufacturerName": "OTT HydroMet",
                    "InstallationDate": "2015-03-20",
                    "LastInspectionDate": "2024-10-15",
                    "MaintenanceSchedule": "Quarterly",
                    "OperationalStatus": "Fully operational",
                    "CertificationStatus": "Fully certified",
                    "GaugeLatitude": 51.4613,
                    "GaugeLongitude": -0.3037,
                    "GroundLevelMeters": 7.5,
                    "elevation": 7.5
                },
                "Measurements": {
                    "MeasurementFrequency": "15 minutes",
                    "MeasurementMethod": "Automatic",
                    "DataTransmission": "Automatic",
                    "DataCurator": "Environment Agency",
                    "DataAccessMethod": "API"
                }
            },
            "FloodStage": {
                "UK": {
                    "DecisionBody": "Environment Agency",
                    "FloodAlert": 4.5,
                    "FloodWarning": 5.5,
                    "SevereFloodWarning": 6.5
                }
            },
            "NRFAMetadata": {
                "NRFAStationID": "NRFA-TEST-001",
                "GridReference": "TQ177746",
                "CatchmentArea": 9.8,
                "RecordStartDate": "2015-03-20",
                "RecordEndDate": "2024-12-31",
                "MeanFlow": 4.2,
                "MedianFlow": 3.8,
                "Q95Flow": 1.5,
                "Q5Flow": 8.9,
                "MaxRecordedFlow": 12.3,
                "MaxRecordedFlowDate": "2024-01-15",
                "HistoricalDataFile": "test_gauge_history.csv",
                "DatabaseSource": "NRFA",
                "FlowUnits": "m3/s",
                "DataQualityNotes": "Good quality"
            },
            "Location": {
                "GaugeLatitude": 51.4613,
                "GaugeLongitude": -0.3037,
                "GaugeElevation": 7.5
            },
            "FloodStages": {
                "FloodAlert": 4.5,
                "FloodWarning": 5.5,
                "SevereFloodWarning": 6.5,
                "HistoricalHighLevel": 6.85,
                "HistoricalHighDate": "2024-01-15"
            }
        }
    }


@pytest.fixture
def gauges_list_data() -> Dict[str, Any]:
    """Multiple gauges wrapped in 'flood_gauges' list."""
    return {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {
                        "GaugeID": "GAUGE-001",
                        "GaugeName": "Gauge One"
                    }
                }
            },
            {
                "FloodGauge": {
                    "Header": {
                        "GaugeID": "GAUGE-002",
                        "GaugeName": "Gauge Two"
                    }
                }
            },
        ]
    }


# ---------------------------------------------------------------------------
# TestFindGaugeById
# ---------------------------------------------------------------------------

class TestFindGaugeById:
    """Tests for the _find_gauge_by_id helper function."""

    def test_find_in_flood_gauges_key(self, gauges_list_data):
        """Dict with 'flood_gauges' list → finds correct gauge by ID."""
        result = _find_gauge_by_id(gauges_list_data, "GAUGE-002")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "GAUGE-002"

    def test_find_first_in_flood_gauges_list(self, gauges_list_data):
        """Dict with 'flood_gauges' list → finds first gauge correctly."""
        result = _find_gauge_by_id(gauges_list_data, "GAUGE-001")
        assert result["FloodGauge"]["Header"]["GaugeName"] == "Gauge One"

    def test_find_single_gauge_object(self, sample_gauge_data):
        """Dict with 'FloodGauge' key (single object) → returns the dict itself."""
        result = _find_gauge_by_id(sample_gauge_data, "GAUGE-test0001")
        # For a single-gauge dict the function returns the dict directly
        assert result is sample_gauge_data

    def test_find_in_list(self):
        """Plain list of gauge dicts → finds the correct one."""
        gauges = [
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-A"}}},
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-B"}}},
        ]
        result = _find_gauge_by_id(gauges, "GAUGE-B")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "GAUGE-B"

    def test_not_found_raises_value_error(self, gauges_list_data):
        """Gauge ID not present in data → ValueError raised."""
        with pytest.raises(ValueError, match="not found"):
            _find_gauge_by_id(gauges_list_data, "GAUGE-999")

    def test_not_found_in_list_raises_value_error(self):
        """Gauge ID not in plain list → ValueError raised."""
        gauges = [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-X"}}}]
        with pytest.raises(ValueError, match="not found"):
            _find_gauge_by_id(gauges, "GAUGE-MISSING")

    def test_invalid_type_raises_value_error(self):
        """Passing a string instead of dict/list → ValueError raised."""
        with pytest.raises(ValueError, match="must be dict or list"):
            _find_gauge_by_id("not-a-valid-structure", "GAUGE-001")

    def test_invalid_dict_raises_value_error(self):
        """Dict with neither 'flood_gauges' nor 'FloodGauge' key → ValueError raised."""
        with pytest.raises(ValueError, match="Invalid gauge data structure"):
            _find_gauge_by_id({"some_other_key": []}, "GAUGE-001")


# ---------------------------------------------------------------------------
# TestAutoOpen
# ---------------------------------------------------------------------------

class TestAutoOpen:
    """Tests for the auto_open=True path in generate_gauge_report."""

    def test_auto_open_called(self, tmp_path, sample_gauge_data):
        """auto_open=True enters the auto-open block (lines 324-325).

        The import ``from .report_generator import open_pdf_file`` fails with
        ModuleNotFoundError (no such module in gauge package), which is caught
        by the ``except Exception`` handler — so the PDF is still returned.
        """
        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            auto_open=True,
        )
        # PDF generated successfully despite the ImportError in auto_open block
        assert report_path is not None
        assert Path(report_path).exists()

    def test_auto_open_success(self, tmp_path, sample_gauge_data):
        """auto_open=True with a successful open_pdf_file call (lines 324-325)."""
        import sys
        import types
        from unittest.mock import MagicMock

        mock_open = MagicMock(return_value=None)
        fake_mod = types.ModuleType("reports.gauge.report_generator")
        fake_mod.open_pdf_file = mock_open

        with patch.dict(sys.modules, {"reports.gauge.report_generator": fake_mod}):
            report_path = generate_gauge_report(
                gauge_data=sample_gauge_data,
                output_dir=tmp_path,
                auto_open=True,
            )

        assert report_path is not None
        assert Path(report_path).exists()
        mock_open.assert_called_once()

    def test_auto_open_false_does_not_raise(self, tmp_path, sample_gauge_data):
        """auto_open=False (default) — no open attempt, returns PDF path normally."""
        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            auto_open=False,
        )
        assert report_path is not None
        assert Path(report_path).exists()
