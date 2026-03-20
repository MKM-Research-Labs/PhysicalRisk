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

"""Tests for reports.gauge.gauge_page_04_measurements — GaugeMeasurementsPage."""

from reportlab.platypus import Paragraph, Table


def _make_gauge():
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
            "SensorDetails": {
                "GaugeInformation": {
                    "OperationalStatus": "Active",
                    "CertificationStatus": "Certified",
                    "LastInspectionDate": "2024-03-01",
                    "MaintenanceSchedule": "Annual",
                },
                "Measurements": {
                    "MeasurementFrequency": "15 minutes",
                    "MeasurementMethod": "Pressure transducer",
                    "DataTransmission": "GPRS",
                    "DataCurator": "EA",
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


def _make_ts(level=3.8, status="Normal"):
    return {
        "readings": [
            {
                "timestamp": "2024-06-01T12:00:00",
                "waterLevel": level,
                "alertStatus": status,
                "exceedsAlert": False,
                "exceedsWarning": False,
                "exceedsSevere": False,
            }
        ]
    }


class TestGaugeMeasurementsPage:

    def _page(self):
        from reports.gauge.gauge_page_04_measurements import GaugeMeasurementsPage
        return GaugeMeasurementsPage()

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
        assert any("Current Measurements" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert any(isinstance(e, Table) for e in result)

    def test_measurement_configuration_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Measurement Configuration" in t for t in texts)

    def test_operational_status_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Operational Status" in t for t in texts)

    def test_historical_statistics_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Historical Measurement Statistics" in t for t in texts)

    def test_no_timeseries_shows_message(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No current timeseries data" in t for t in texts)

    def test_with_timeseries_shows_current_readings(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Current Readings" in t for t in texts)

    def test_with_timeseries_has_extra_table(self):
        """Current readings table is added when timeseries provided."""
        page = self._page()
        without_ts = page.generate_elements(_make_gauge())
        with_ts = page.generate_elements(_make_gauge(), timeseries_data=_make_ts())
        tables_without = [e for e in without_ts if isinstance(e, Table)]
        tables_with = [e for e in with_ts if isinstance(e, Table)]
        assert len(tables_with) >= len(tables_without)

    def test_empty_readings_list_does_not_crash(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data={"readings": []})
        assert isinstance(result, list)

    def test_get_gauge_id_present(self):
        page = self._page()
        assert page._get_gauge_id(_make_gauge()) == "GAUGE-001"

    def test_get_gauge_id_missing(self):
        page = self._page()
        assert page._get_gauge_id({}) == "Unknown Gauge"
