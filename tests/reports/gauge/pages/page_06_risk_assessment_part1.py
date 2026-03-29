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

"""Tests for GaugeRiskAssessmentPage — basic, score, distance, frequency, historical."""

import pytest

from tests.reports.gauge.pages.conftest import _make_gauge_data, _make_timeseries


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
