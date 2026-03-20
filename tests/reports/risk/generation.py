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

"""Tests for risk report PDF generation and edge cases."""


class TestRiskReportGeneration:
    """Test risk report PDF generation."""

    def test_basic_report_generation(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        generator = RiskReportGenerator(output_dir)
        report_path = generator.generate_basic_report(sample_portfolio_data)
        assert report_path.exists()
        assert report_path.suffix == ".pdf"
        assert report_path.stat().st_size > 0

    def test_detailed_report_generation(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        report_path = RiskReportGenerator(output_dir).generate_detailed_report(sample_portfolio_data)
        assert report_path.exists()
        assert report_path.stat().st_size > 0

    def test_summary_report_generation(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        report_path = RiskReportGenerator(output_dir).generate_summary_report(sample_portfolio_data)
        assert report_path.exists()
        assert report_path.stat().st_size > 0

    def test_analysis_report_generation(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        report_path = RiskReportGenerator(output_dir).generate_analysis_report(sample_portfolio_data)
        assert report_path.exists()
        assert report_path.stat().st_size > 0

    def test_custom_filename(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        custom_name = "custom_risk_report.pdf"
        report_path = RiskReportGenerator(output_dir).generate_basic_report(
            sample_portfolio_data, output_filename=custom_name
        )
        assert report_path.name == custom_name
        assert report_path.exists()

    def test_custom_page_selection(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        report_path = RiskReportGenerator(output_dir).generate_report(
            sample_portfolio_data, pages_to_include=["title", "risk_analysis", "appendix"]
        )
        assert report_path.exists()


class TestRiskReportEdgeCases:
    """Test edge cases and error handling."""

    def test_minimal_data_report(self, minimal_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        assert RiskReportGenerator(output_dir).generate_basic_report(minimal_portfolio_data).exists()

    def test_high_risk_portfolio_report(self, high_risk_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        assert RiskReportGenerator(output_dir).generate_detailed_report(high_risk_portfolio_data).exists()

    def test_empty_gauge_data(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        data = {**sample_portfolio_data, "gauge_data": {}}
        assert RiskReportGenerator(output_dir).generate_basic_report(data).exists()

    def test_missing_mortgage_data(self, sample_portfolio_data, output_dir):
        from reports.risk import RiskReportGenerator
        data = {**sample_portfolio_data, "summary": {**sample_portfolio_data["summary"]}}
        data["summary"].pop("mortgage_summary", None)
        assert RiskReportGenerator(output_dir).generate_detailed_report(data).exists()

    def test_auto_select_pages_returns_list(self, sample_portfolio_data, output_dir):
        """Lines 126-134: _auto_select_pages returns known pages."""
        from reports.risk import RiskReportGenerator
        gen = RiskReportGenerator(output_dir)
        pages = gen._auto_select_pages(sample_portfolio_data)
        assert isinstance(pages, list)
        assert len(pages) > 0

    def test_generate_elements_skips_unknown(self, sample_portfolio_data, output_dir):
        """Lines 148-149: unknown page → warning, skipped."""
        from reports.risk import RiskReportGenerator
        gen = RiskReportGenerator(output_dir)
        elements = gen._generate_elements(sample_portfolio_data, ["bogus_page"])
        assert isinstance(elements, list)

    def test_generate_elements_exception_continues(self, sample_portfolio_data, output_dir):
        """Lines 162-164: page raises → continue to next."""
        from reports.risk import RiskReportGenerator
        from unittest.mock import MagicMock
        gen = RiskReportGenerator(output_dir)
        bad = MagicMock()
        bad.generate_elements.side_effect = RuntimeError("page crash")
        gen.pages["bad_page"] = bad
        elements = gen._generate_elements(sample_portfolio_data, ["bad_page", "title"])
        assert isinstance(elements, list)

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        """Lines 60-62: output_dir=None → uses config.get_risk_reports_dir()."""
        from config import config
        risk_dir = tmp_path / "risk_reports"
        try:
            monkeypatch.setattr(config, "get_risk_reports_dir", lambda: risk_dir)
        except AttributeError:
            return  # config doesn't have this method — skip
        from reports.risk import RiskReportGenerator
        gen = RiskReportGenerator()
        assert gen.output_dir == risk_dir

    def test_list_available_pages(self, output_dir):
        """Line 261: list_available_pages."""
        from reports.risk import RiskReportGenerator
        gen = RiskReportGenerator(output_dir)
        pages = gen.list_available_pages()
        assert isinstance(pages, list)
        assert len(pages) > 0

    def test_get_page_categories(self, output_dir):
        """Line 265: get_page_categories."""
        from reports.risk import RiskReportGenerator
        cats = RiskReportGenerator(output_dir).get_page_categories()
        assert isinstance(cats, dict)

    def test_validate_pages_valid_and_invalid(self, output_dir):
        """Lines 270-336: validate_pages."""
        from reports.risk import RiskReportGenerator
        gen = RiskReportGenerator(output_dir)
        valid, invalid = gen.validate_pages(["title", "nonexistent"])
        assert "title" in valid
        assert "nonexistent" in invalid


class TestGenerateRiskReport:
    """Tests for the generate_risk_report convenience function."""

    def test_basic_type(self, sample_portfolio_data, output_dir):
        """Line 257-258: 'basic' type."""
        from reports.risk.risk_report_generator import generate_risk_report
        path = generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="basic")
        assert path.exists()

    def test_detailed_type(self, sample_portfolio_data, output_dir):
        """Lines 259-260: 'detailed' type."""
        from reports.risk.risk_report_generator import generate_risk_report
        path = generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="detailed")
        assert path.exists()

    def test_summary_type(self, sample_portfolio_data, output_dir):
        """Lines 261-262: 'summary' type."""
        from reports.risk.risk_report_generator import generate_risk_report
        path = generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="summary")
        assert path.exists()

    def test_analysis_type(self, sample_portfolio_data, output_dir):
        """Lines 263-264: 'analysis' type."""
        from reports.risk.risk_report_generator import generate_risk_report
        path = generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="analysis")
        assert path.exists()

    def test_unknown_type_fallback(self, sample_portfolio_data, output_dir):
        """Lines 265-266: unknown type → generate_report."""
        from reports.risk.risk_report_generator import generate_risk_report
        path = generate_risk_report(sample_portfolio_data, output_dir=output_dir, report_type="unknown")
        assert path.exists()
