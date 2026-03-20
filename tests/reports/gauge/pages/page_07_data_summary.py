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

"""Tests for reports.gauge.gauge_page_07_data_summary — GaugeDataSummaryPage."""

from reportlab.platypus import Paragraph, Table


def _make_gauge(risk_cat="High", risk_score=7.5, hist_high=6.5, freq=3,
                op_status="Operational", cert="Certified"):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Chelsea Bridge"},
            "SensorDetails": {
                "GaugeInformation": {
                    "GaugeType": "Stage",
                    "ManufacturerName": "OTT Hydromet",
                    "OperationalStatus": op_status,
                    "CertificationStatus": cert,
                    "InstallationDate": "2005-06-01",
                    "GaugeLatitude": 51.488,
                    "GaugeLongitude": -0.166,
                    "MaintenanceSchedule": "Annual",
                },
                "Measurements": {
                    "MeasurementFrequency": "15 minutes",
                    "DataTransmission": "GPRS",
                },
            },
            "SensorStats": {
                "HistoricalHighLevel": hist_high,
                "FrequencyExceedLevel3": freq,
            },
            "FloodStage": {
                "UK": {
                    "FloodAlert": 3.5,
                    "FloodWarning": 4.5,
                    "SevereFloodWarning": 5.5,
                }
            },
            "ThamesInfo": {
                "FloodRiskAssessment": {
                    "FloodRiskScore": risk_score,
                    "FloodRiskCategory": risk_cat,
                }
            },
        }
    }


def _make_ts(status="Normal", level=3.0):
    return {
        "readings": [
            {"waterLevel": level, "alertStatus": status, "timestamp": "2024-06-01T12:00:00"}
        ]
    }


class TestGaugeDataSummaryPage:

    def _page(self):
        from reports.gauge.gauge_page_07_data_summary import GaugeDataSummaryPage
        return GaugeDataSummaryPage()

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
        assert any("Comprehensive Data Summary" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert any(isinstance(e, Table) for e in result)

    def test_gauge_overview_summary_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Gauge Overview Summary" in t for t in texts)

    def test_key_metrics_summary_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Key Metrics Summary" in t for t in texts)

    def test_operational_status_summary_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Operational Status Summary" in t for t in texts)

    def test_report_conclusions_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Report Conclusions" in t for t in texts)

    def test_hist_high_exceeds_severe_significance(self):
        """hist_high > severe_level → 'Exceeds severe warning' significance."""
        page = self._page()
        result = page.generate_elements(_make_gauge(hist_high=6.5))
        assert "Exceeds severe warning" in str(result)

    def test_hist_high_within_range_significance(self):
        """hist_high <= severe_level → 'Within expected range' significance."""
        page = self._page()
        result = page.generate_elements(_make_gauge(hist_high=4.0))
        assert "Within expected range" in str(result)

    def test_freq_zero_significance(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(freq=0))
        assert "No severe exceedances" in str(result)

    def test_freq_low_significance(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(freq=1))
        assert "Low frequency events" in str(result)

    def test_freq_high_significance(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(freq=5))
        assert "Regular severe events" in str(result)

    def test_high_risk_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(risk_cat="high"))
        assert "high flood risk" in str(result)

    def test_moderate_risk_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(risk_cat="moderate"))
        assert "Moderate flood risk" in str(result)

    def test_low_risk_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(risk_cat="low"))
        assert "Low flood risk" in str(result)

    def test_operational_status_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(op_status="Operational"))
        assert "fully operational" in str(result)

    def test_certified_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(cert="certified"))
        assert "certification standards" in str(result)

    def test_freq_zero_no_exceedances_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(freq=0))
        assert "No historical severe flood events" in str(result)

    def test_timeseries_normal_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts("normal"))
        assert "normal water levels" in str(result)

    def test_timeseries_severe_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts("severe"))
        assert "CRITICAL" in str(result)

    def test_timeseries_warning_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts("warning"))
        assert "WARNING" in str(result)

    def test_timeseries_alert_conclusion(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts("alert"))
        assert "ALERT" in str(result)

    def test_get_gauge_id_present(self):
        page = self._page()
        assert page._get_gauge_id(_make_gauge()) == "GAUGE-001"

    def test_get_gauge_id_missing(self):
        page = self._page()
        assert page._get_gauge_id({}) == "Unknown Gauge"

    def test_get_gauge_name_present(self):
        page = self._page()
        assert page._get_gauge_name(_make_gauge()) == "Chelsea Bridge"

    def test_get_gauge_name_missing(self):
        page = self._page()
        assert page._get_gauge_name({}) == "Unknown Gauge Name"
