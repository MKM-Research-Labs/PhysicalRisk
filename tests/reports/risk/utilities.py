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

"""Tests for report utility functions, convenience function, and workflow."""


class TestRiskReportUtilities:
    """Test report generator utility functions."""

    def test_list_available_pages(self):
        from reports.risk import RiskReportGenerator
        pages = RiskReportGenerator().list_available_pages()
        assert isinstance(pages, list)
        for key in ("title", "executive_summary", "risk_analysis", "appendix"):
            assert key in pages

    def test_get_page_categories(self):
        from reports.risk import RiskReportGenerator
        categories = RiskReportGenerator().get_page_categories()
        assert isinstance(categories, dict)
        for key in ("overview", "analysis", "appendix"):
            assert key in categories

    def test_validate_pages_valid(self):
        from reports.risk import RiskReportGenerator
        valid, invalid = RiskReportGenerator().validate_pages(["title", "risk_analysis"])
        assert len(valid) == 2
        assert len(invalid) == 0

    def test_validate_pages_invalid(self):
        from reports.risk import RiskReportGenerator
        valid, invalid = RiskReportGenerator().validate_pages(["title", "nonexistent_page"])
        assert "title" in valid
        assert "nonexistent_page" in invalid


class TestConvenienceFunction:
    """Test convenience function for report generation."""

    def test_generate_risk_report_basic(self, sample_portfolio_data, output_dir):
        from reports.risk import generate_risk_report
        assert generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="basic").exists()

    def test_generate_risk_report_detailed(self, sample_portfolio_data, output_dir):
        from reports.risk import generate_risk_report
        assert generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="detailed").exists()

    def test_generate_risk_report_default(self, sample_portfolio_data, output_dir):
        from reports.risk import generate_risk_report
        assert generate_risk_report(sample_portfolio_data, output_dir=output_dir).exists()


class TestRiskBasePageFormatters:
    """Tests for RiskBasePage formatter methods (lines 202-257)."""

    @staticmethod
    def _page():
        from reports.risk.risk_page_01_title import RiskTitlePage
        return RiskTitlePage()

    def test_format_field_name_camel_case(self):
        """Lines 204-215: camelCase → 'Camel Case'."""
        page = self._page()
        result = page._format_field_name("riskLevel")
        assert "Risk" in result

    def test_format_field_name_replacements(self):
        """Lines 207-213: abbreviation replacements applied."""
        page = self._page()
        result = page._format_field_name("propertyId")
        assert "ID" in result

    def test_format_value_none(self):
        """Line 220: None → 'Not specified'."""
        page = self._page()
        assert page._format_value(None) == "Not specified"

    def test_format_value_bool_true(self):
        """Line 222: True → 'Yes'."""
        page = self._page()
        assert page._format_value(True) == "Yes"

    def test_format_value_bool_false(self):
        """Line 222: False → 'No'."""
        page = self._page()
        assert page._format_value(False) == "No"

    def test_format_value_float_integer(self):
        """Lines 224-225: float with no fractional part → int string."""
        page = self._page()
        assert page._format_value(5.0) == "5"

    def test_format_value_float_decimal(self):
        """Lines 226-227: float with fractional part → 2dp string."""
        page = self._page()
        result = page._format_value(3.14159)
        assert result == "3.14"

    def test_format_value_int(self):
        """Lines 228-229: integer → plain string."""
        page = self._page()
        assert page._format_value(42) == "42"

    def test_format_value_empty_string(self):
        """Lines 230-231: blank string → 'Not specified'."""
        page = self._page()
        assert page._format_value("   ") == "Not specified"

    def test_format_value_non_empty_string(self):
        """Lines 232-233: non-empty string → passed through."""
        page = self._page()
        assert page._format_value("hello") == "hello"

    def test_format_currency_numeric(self):
        """Line 238: numeric → £ formatted."""
        page = self._page()
        result = page._format_currency(1234567.89)
        assert "£" in result
        assert "1,234,567" in result

    def test_format_currency_non_numeric(self):
        """Line 239: non-numeric → delegates to _format_value."""
        page = self._page()
        result = page._format_currency(None)
        assert result == "Not specified"

    def test_format_percentage_numeric(self):
        """Line 244: numeric → formatted with %."""
        page = self._page()
        result = page._format_percentage(12.345)
        assert "%" in result
        assert "12.3" in result

    def test_format_percentage_non_numeric(self):
        """Line 245: non-numeric → delegates to _format_value."""
        page = self._page()
        assert page._format_percentage(None) == "Not specified"

    def test_format_depth_numeric(self):
        """Line 250: numeric → formatted with 'm'."""
        page = self._page()
        result = page._format_depth(1.5)
        assert "1.50m" in result

    def test_format_depth_non_numeric(self):
        """Line 251: non-numeric → delegates to _format_value."""
        page = self._page()
        assert page._format_depth("N/A") == "N/A"

    def test_format_count_numeric(self):
        """Line 256: numeric → comma-formatted."""
        page = self._page()
        result = page._format_count(1234567)
        assert "1,234,567" in result

    def test_format_count_non_numeric(self):
        """Line 257: non-numeric → delegates to _format_value."""
        page = self._page()
        assert page._format_count(None) == "Not specified"


class TestRiskReportWorkflow:
    """Integration tests for complete report workflow."""

    def test_complete_workflow_basic(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        report_path = RiskReportGenerator(output_dir).generate_basic_report(sample_portfolio_data)
        assert report_path.exists()
        assert report_path.suffix == ".pdf"
        assert report_path.stat().st_size > 10_000

    def test_complete_workflow_all_types(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        gen = RiskReportGenerator(output_dir)
        basic = gen.generate_basic_report(sample_portfolio_data)
        detailed = gen.generate_detailed_report(sample_portfolio_data)
        summary = gen.generate_summary_report(sample_portfolio_data)
        analysis = gen.generate_analysis_report(sample_portfolio_data)
        for p in (basic, detailed, summary, analysis):
            assert p.exists()
            assert p.stat().st_size > 0
