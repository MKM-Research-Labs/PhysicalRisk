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

"""Tests for reports.gauge.gauge_page_02_sensor_details — GaugeSensorDetailsPage."""

from reportlab.platypus import Paragraph, Table


def _make_gauge():
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
            "SensorDetails": {
                "GaugeInformation": {
                    "DataSourceType": "Telemetry",
                    "GaugeOwner": "Environment Agency",
                    "GaugeType": "Stage",
                    "ManufacturerName": "OTT Hydromet",
                    "InstallationDate": "2010-05-01",
                    "LastInspectionDate": "2024-03-01",
                    "MaintenanceSchedule": "Annual",
                    "OperationalStatus": "Active",
                    "CertificationStatus": "Certified",
                    "GaugeLatitude": 51.508,
                    "GaugeLongitude": -0.121,
                    "GroundLevelMeters": 4.5,
                },
                "Measurements": {
                    "MeasurementFrequency": "15 minutes",
                    "MeasurementMethod": "Pressure transducer",
                    "DataTransmission": "GPRS",
                    "DataCurator": "EA National Flood Forecasting",
                    "DataAccessMethod": "API",
                },
            },
            "SensorStats": {
                "HistoricalHighLevel": 6.2,
                "HistoricalHighDate": "2014-02-10",
                "LastDateLevelExceedLevel3": "2021-01-05",
                "FrequencyExceedLevel3": 3,
            },
        }
    }


class TestGaugeSensorDetailsPage:

    def _page(self):
        from reports.gauge.gauge_page_02_sensor_details import GaugeSensorDetailsPage
        return GaugeSensorDetailsPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_data_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_title_present(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Sensor Details" in t for t in texts)

    def test_gauge_id_in_subtitle(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("GAUGE-001" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert any(isinstance(e, Table) for e in result)

    def test_gauge_information_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Gauge Information" in t for t in texts)

    def test_location_information_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Location Information" in t for t in texts)

    def test_measurement_configuration_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Measurement Configuration" in t for t in texts)

    def test_historical_sensor_statistics_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Historical Sensor Statistics" in t for t in texts)

    def test_no_sensor_details_does_not_crash(self):
        """Missing SensorDetails → empty tables, no exception."""
        page = self._page()
        result = page.generate_elements({"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}})
        assert isinstance(result, list)

    def test_get_gauge_id_present(self):
        page = self._page()
        assert page._get_gauge_id(_make_gauge()) == "GAUGE-001"

    def test_get_gauge_id_missing(self):
        page = self._page()
        assert page._get_gauge_id({}) == "Unknown Gauge"

    def test_with_timeseries_does_not_crash(self):
        page = self._page()
        ts = {"readings": [{"waterLevel": 3.5}]}
        result = page.generate_elements(_make_gauge(), timeseries_data=ts)
        assert isinstance(result, list)
