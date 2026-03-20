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

"""Tests for reports.gauge.gauge_page_06_risk_assessment — GaugeRiskAssessmentPage."""

import pytest


def _make_gauge_data(
    gauge_id="GAUGE-001",
    risk_score=None,
    risk_category=None,
    distance_to_thames=200,
    freq_exceed=0,
    historical_high=None,
    severe_level=5.0,
    flood_alert=3.5,
    flood_warning=4.5,
    last_exceed_date=None,
):
    flood_risk = {}
    if risk_score is not None:
        flood_risk["FloodRiskScore"] = risk_score
    if risk_category is not None:
        flood_risk["FloodRiskCategory"] = risk_category

    sensor_stats = {"FrequencyExceedLevel3": freq_exceed}
    if historical_high is not None:
        sensor_stats["HistoricalHighLevel"] = historical_high
    if last_exceed_date is not None:
        sensor_stats["LastDateLevelExceedLevel3"] = last_exceed_date

    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id},
            "ThamesInfo": {
                "DistanceToThamesMeters": distance_to_thames,
                "FloodRiskAssessment": flood_risk,
            },
            "SensorStats": sensor_stats,
            "FloodStage": {
                "UK": {
                    "FloodAlert": flood_alert,
                    "FloodWarning": flood_warning,
                    "SevereFloodWarning": severe_level,
                }
            },
        }
    }


def _make_timeseries(level=None, status="Unknown"):
    return {"readings": [{"waterLevel": level, "alertStatus": status}]}


class TestGaugeRiskAssessmentPageBasic:

    def test_generates_elements_list(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data())
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_with_timeseries_data(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(), timeseries_data=_make_timeseries(level=4.0, status="Alert")
        )
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_no_timeseries_shows_placeholder(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        from reportlab.platypus import Paragraph
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(), timeseries_data=None)
        texts = [e.text if hasattr(e, "text") else "" for e in elements]
        assert any("No current timeseries" in t for t in texts)


class TestRiskScoreBranches:

    def _elements(self, score, **kwargs):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        return page.generate_elements(_make_gauge_data(risk_score=score, **kwargs))

    def test_very_high_risk_label(self):
        elements = self._elements(score=9.0)
        assert "Very High Risk" in str(elements)

    def test_high_risk_label(self):
        elements = self._elements(score=7.0)
        assert "High Risk" in str(elements)

    def test_moderate_risk_label(self):
        elements = self._elements(score=5.0)
        assert "Moderate Risk" in str(elements)

    def test_low_risk_label(self):
        elements = self._elements(score=2.0)
        assert "Low Risk" in str(elements)

    def test_non_numeric_score_formatted(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        data = _make_gauge_data()
        data["FloodGauge"]["ThamesInfo"]["FloodRiskAssessment"]["FloodRiskCategory"] = "High"
        elements = page.generate_elements(data)
        assert isinstance(elements, list)


class TestDistanceToThames:

    def test_zero_distance_highest_risk(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(distance_to_thames=0))
        assert "On Thames River" in str(elements)

    def test_close_distance_label(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(distance_to_thames=50))
        assert "Very close to Thames" in str(elements)


class TestFrequencyExceedance:

    def test_zero_exceedances(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(freq_exceed=0))
        assert "No severe level exceedances recorded" in str(elements)

    def test_one_exceedance(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(freq_exceed=1))
        assert "One severe level exceedance" in str(elements)

    def test_two_exceedances_moderate(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(freq_exceed=2))
        assert "Moderate frequency" in str(elements)

    def test_four_exceedances_high(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(_make_gauge_data(freq_exceed=5))
        assert "High frequency" in str(elements)


class TestHistoricalHigh:

    def test_exceeded_severe_label(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(historical_high=6.0, severe_level=5.0)
        )
        assert "Exceeded severe warning level" in str(elements)

    def test_within_severe_level(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(historical_high=4.0, severe_level=5.0)
        )
        assert "4.000m" in str(elements)


class TestLastExceedDate:

    def test_recent_activity_within_1_year(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        from datetime import datetime
        page = GaugeRiskAssessmentPage()
        current_year = datetime.now().year
        elements = page.generate_elements(
            _make_gauge_data(last_exceed_date=f"{current_year}-03-01")
        )
        assert "Recent severe level activity" in str(elements)

    def test_moderate_recent_activity(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        from datetime import datetime
        page = GaugeRiskAssessmentPage()
        year = datetime.now().year - 2
        elements = page.generate_elements(
            _make_gauge_data(last_exceed_date=f"{year}-01-01")
        )
        assert "Moderate recent activity" in str(elements)

    def test_no_recent_activity(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(last_exceed_date="2010-06-15")
        )
        assert "No recent severe activity" in str(elements)

    def test_bad_date_string_gracefully_skipped(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(last_exceed_date="not-a-date")
        )
        assert isinstance(elements, list)


class TestThresholdAnalysis:

    def test_narrow_alert_range(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(flood_alert=4.0, flood_warning=4.5, severe_level=5.0)
        )
        assert "Narrow alert range" in str(elements)

    def test_moderate_alert_range(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(flood_alert=3.0, flood_warning=4.2, severe_level=6.0)
        )
        assert "Moderate alert range" in str(elements)

    def test_wide_alert_range(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(flood_alert=2.0, flood_warning=5.0, severe_level=8.0)
        )
        assert "Wide alert range" in str(elements)

    def test_historical_high_exceeds_severe_by_more_than_1m(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(flood_alert=3.0, flood_warning=4.0, severe_level=5.0,
                             historical_high=7.0)
        )
        assert "High risk" in str(elements)

    def test_historical_high_exceeds_severe_by_less_than_1m(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(flood_alert=3.0, flood_warning=4.0, severe_level=5.0,
                             historical_high=5.5)
        )
        assert "Elevated risk" in str(elements)

    def test_historical_high_within_severe(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(flood_alert=3.0, flood_warning=4.0, severe_level=5.0,
                             historical_high=4.5)
        )
        assert "within severe warning levels" in str(elements)


class TestTimeseriesAlertStatus:

    def _elements(self, status, level=4.0):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        return page.generate_elements(
            _make_gauge_data(), timeseries_data=_make_timeseries(level=level, status=status)
        )

    def test_severe_status(self):
        assert "CRITICAL RISK" in str(self._elements("Severe"))

    def test_warning_status(self):
        assert "HIGH RISK" in str(self._elements("Warning"))

    def test_alert_status(self):
        assert "ELEVATED RISK" in str(self._elements("Alert"))

    def test_normal_status(self):
        assert "NORMAL" in str(self._elements("Normal"))

    def test_timeseries_with_no_level(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(), timeseries_data=_make_timeseries(level=None, status="Alert")
        )
        assert isinstance(elements, list)

    def test_timeseries_with_no_readings(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(
            _make_gauge_data(), timeseries_data={"readings": []}
        )
        assert isinstance(elements, list)


class TestExceptionHandling:

    def test_malformed_gauge_data_returns_error_element(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        elements = page.generate_elements(None)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_get_gauge_id_missing_key(self):
        from reports.gauge.gauge_page_06_risk_assessment import GaugeRiskAssessmentPage
        page = GaugeRiskAssessmentPage()
        assert page._get_gauge_id({}) == "Unknown Gauge"
        assert page._get_gauge_id(None) == "Unknown Gauge"
