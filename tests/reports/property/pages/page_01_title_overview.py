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

"""Tests for reports.property.property_page_01_title_overview — TitleOverviewPage."""

from reportlab.platypus import Paragraph, Table


def _make_property():
    return {
        "PropertyHeader": {
            "Header": {
                "PropertyID": "PROP-001",
                "UPRN": "12345678",
                "PropertyType": "Residential",
                "PropertyStatus": "Active",
                "DateCreated": "2020-01-01",
                "LastUpdated": "2024-06-01",
            },
            "PropertyAttributes": {
                "PropertyType": "Semi-detached",
                "PropertyAreaSqm": 120.0,
                "NumberBedrooms": 3,
                "NumberBathrooms": 2,
                "PropertyCondition": "Good",
                "CouncilTaxBand": "D",
                "ConstructionYear": 1990,
            },
        }
    }


class TestTitleOverviewPage:

    def _page(self):
        from reports.property.property_page_01_title_overview import TitleOverviewPage
        return TitleOverviewPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_property_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_has_title_paragraph(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Comprehensive Property Analysis Report" in t for t in texts)

    def test_property_id_in_output(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("PROP-001" in t for t in texts)

    def test_unknown_property_id_fallback(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Unknown Property" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_property_overview_section_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Property Overview" in t for t in texts)

    def test_property_summary_section_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Property Summary" in t for t in texts)

    def test_building_age_calculated(self):
        """ConstructionYear triggers building age row in summary table."""
        page = self._page()
        result = page.generate_elements(_make_property())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_with_mortgage_data_does_not_crash(self):
        page = self._page()
        mortgage = {"RLoan": {"Header": {"RLoanID": "MORT-001"}}}
        result = page.generate_elements(_make_property(), mortgage)
        assert isinstance(result, list)

    def test_get_property_id_missing_nested_key(self):
        """Missing nested key falls back to 'Unknown Property'."""
        page = self._page()
        result = page._get_property_id({"PropertyHeader": {}})
        assert result == "Unknown Property"

    def test_get_property_id_present(self):
        page = self._page()
        result = page._get_property_id(_make_property())
        assert result == "PROP-001"
