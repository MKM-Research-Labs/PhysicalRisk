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

"""Tests for reports.property.property_page_15_data_summary — DataSummaryPage."""

from reportlab.platypus import Paragraph, Table


def _make_property(with_sections=True):
    if not with_sections:
        return {}
    return {
        "PropertyHeader": {
            "PropertyID": "PROP-001",
            "Address": "1 Test Street",
            "RiskAssessment": {"OverallFloodRisk": "Medium"},
        },
        "ProtectionMeasures": {
            "FloodGates": True,
            "SumpPump": None,
        },
        "TransactionHistory": {
            "Sales": {"SalePriceGbp": 600_000},
        },
    }


def _make_property_with_header():
    return {
        "PropertyHeader": {
            "Header": {
                "PropertyID": "PROP-999",
                "UPRN": "123456789",
                "LastUpdated": "2025-01-01",
            },
        }
    }


def _make_mortgage():
    return {
        "Mortgage": {
            "Header": {"MortgageID": "MORT-001"},
            "CurrentStatus": {
                "CurrentLTV": 0.65,
                "InArrearsFlag": False,
            },
        }
    }


class TestDataSummaryPageBasics:

    def _page(self):
        from reports.property.property_page_15_data_summary import DataSummaryPage
        return DataSummaryPage()

    def test_returns_list(self):
        assert isinstance(self._page().generate_elements(_make_property()), list)

    def test_returns_non_empty(self):
        assert len(self._page().generate_elements(_make_property())) > 0

    def test_has_data_header(self):
        result = self._page().generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Data" in t for t in texts)

    def test_has_table(self):
        result = self._page().generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_empty_property_does_not_crash(self):
        assert isinstance(self._page().generate_elements({}), list)

    def test_with_mortgage_data(self):
        result = self._page().generate_elements(_make_property(), _make_mortgage())
        assert isinstance(result, list) and len(result) > 0

    def test_both_empty(self):
        assert isinstance(self._page().generate_elements({}, {}), list)

    def test_no_sections_in_property(self):
        result = self._page().generate_elements(_make_property(with_sections=False))
        assert isinstance(result, list)


class TestAnalyzeDataCompleteness:

    def _page(self):
        from reports.property.property_page_15_data_summary import DataSummaryPage
        return DataSummaryPage()

    def test_returns_dict(self):
        r = self._page()._analyze_data_completeness(_make_property())
        assert isinstance(r, dict)

    def test_property_header_section_present(self):
        prop = {"PropertyHeader": {"A": 1, "B": None}}
        r = self._page()._analyze_data_completeness(prop)
        assert "PropertyHeader" in r

    def test_section_not_present_excluded(self):
        r = self._page()._analyze_data_completeness({})
        assert len(r) == 0

    def test_mortgage_data_included(self):
        r = self._page()._analyze_data_completeness({}, _make_mortgage())
        assert "Mortgage Data" in r

    def test_completeness_percentage_computed(self):
        prop = {"PropertyHeader": {"A": 1, "B": 2, "C": None}}
        r = self._page()._analyze_data_completeness(prop)
        assert r["PropertyHeader"]["percentage"] == pytest.approx(66.67, abs=1)

    def test_empty_section_excluded(self):
        prop = {"PropertyHeader": {}}
        r = self._page()._analyze_data_completeness(prop)
        # Empty dict has no fields, so shouldn't be added
        assert "PropertyHeader" not in r


class TestAssessDataQuality:

    def _page(self):
        from reports.property.property_page_15_data_summary import DataSummaryPage
        return DataSummaryPage()

    def test_excellent_over_90(self):
        r = self._page()._assess_data_quality(95.0, {})
        assert "Excellent" in r["Overall Completeness"]

    def test_good_75_to_90(self):
        r = self._page()._assess_data_quality(80.0, {})
        assert "Good" in r["Overall Completeness"]

    def test_fair_60_to_75(self):
        r = self._page()._assess_data_quality(65.0, {})
        assert "Fair" in r["Overall Completeness"]

    def test_limited_40_to_60(self):
        r = self._page()._assess_data_quality(50.0, {})
        assert "Limited" in r["Overall Completeness"]

    def test_poor_under_40(self):
        r = self._page()._assess_data_quality(30.0, {})
        assert "Poor" in r["Overall Completeness"]

    def test_best_and_worst_sections_shown(self):
        stats = {
            "SectionA": {"percentage": 90.0},
            "SectionB": {"percentage": 50.0},
        }
        r = self._page()._assess_data_quality(70.0, stats)
        assert "Best Data Section" in r
        assert "Weakest Data Section" in r

    def test_critical_completeness_high(self):
        stats = {"PropertyHeader": {"percentage": 85.0}}
        r = self._page()._assess_data_quality(85.0, stats)
        assert "Critical Data Reliability" in r
        assert "High" in r["Critical Data Reliability"]

    def test_critical_completeness_medium(self):
        stats = {"PropertyHeader": {"percentage": 65.0}}
        r = self._page()._assess_data_quality(65.0, stats)
        assert "Medium" in r["Critical Data Reliability"]

    def test_critical_completeness_low(self):
        stats = {"PropertyHeader": {"percentage": 40.0}}
        r = self._page()._assess_data_quality(40.0, stats)
        assert "Low" in r["Critical Data Reliability"]


class TestGenerateReportMetadata:

    def _page(self):
        from reports.property.property_page_15_data_summary import DataSummaryPage
        return DataSummaryPage()

    def test_returns_dict(self):
        r = self._page()._generate_report_metadata({})
        assert isinstance(r, dict)

    def test_has_report_generated_timestamp(self):
        r = self._page()._generate_report_metadata({})
        assert "Report Generated" in r

    def test_property_id_extracted(self):
        r = self._page()._generate_report_metadata(_make_property_with_header())
        assert r["Property ID"] == "PROP-999"

    def test_uprn_extracted(self):
        r = self._page()._generate_report_metadata(_make_property_with_header())
        assert r["UPRN"] == "123456789"

    def test_last_updated_extracted(self):
        r = self._page()._generate_report_metadata(_make_property_with_header())
        assert r["Data Last Updated"] == "2025-01-01"

    def test_unknown_property_id_when_missing(self):
        r = self._page()._generate_report_metadata({})
        assert r["Property ID"] == "Unknown"

    def test_scope_property_only(self):
        r = self._page()._generate_report_metadata({})
        assert "Property-Only" in r["Analysis Scope"]

    def test_scope_combined_with_mortgage(self):
        r = self._page()._generate_report_metadata({}, _make_mortgage())
        assert "Mortgage" in r["Analysis Scope"]

    def test_mortgage_id_extracted(self):
        r = self._page()._generate_report_metadata({}, _make_mortgage())
        assert r.get("Mortgage ID") == "MORT-001"


class TestGenerateDataRecommendations:

    def _page(self):
        from reports.property.property_page_15_data_summary import DataSummaryPage
        return DataSummaryPage()

    def test_returns_list(self):
        r = self._page()._generate_data_recommendations({})
        assert isinstance(r, list)

    def test_poor_section_under_50_gets_recommendation(self):
        stats = {"SomeSection": {"percentage": 30.0}}
        r = self._page()._generate_data_recommendations(stats)
        assert any("SomeSection" in rec for rec in r)

    def test_fair_section_50_to_75_gets_enhancement_rec(self):
        stats = {"OtherSection": {"percentage": 60.0}}
        r = self._page()._generate_data_recommendations(stats)
        assert any("OtherSection" in rec for rec in r)

    def test_good_sections_maintain_recommendation(self):
        stats = {"Section": {"percentage": 95.0}}
        r = self._page()._generate_data_recommendations(stats)
        assert any("Maintain" in rec or "maintain" in rec for rec in r)

    def test_max_5_recommendations(self):
        stats = {f"Section{i}": {"percentage": 20.0} for i in range(10)}
        r = self._page()._generate_data_recommendations(stats)
        assert len(r) <= 5


# need pytest for approx
import pytest
