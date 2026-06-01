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

"""
Tests for PropertyReportGenerator and generate_property_report.

Covers: direct generator methods (list_available_pages, get_page_categories,
validate_pages, auto_select_pages, generate_elements, focused reports) and
the convenience function generate_property_report (report types, auto_open).
"""

from unittest.mock import MagicMock, patch


# ===========================================================================
# Shared test data
# ===========================================================================

_PROP_DATA = {
    "PropertyHeader": {
        "PropertyID": "PROP-TEST",
        "RiskAssessment": {"OverallFloodRisk": "Low"},
        "Valuation": {"PropertyValue": 400_000},
    }
}
_MORT_DATA = {
    "Mortgage": {
        "Header": {"MortgageID": "MORT-001", "PropertyID": "PROP-TEST"},
        "FinancialTerms": {"OriginalLoan": 200_000},
        "CurrentStatus": {"OutstandingBalance": 180_000},
    }
}


# ===========================================================================
# PropertyReportGenerator — direct tests for uncovered branches
# ===========================================================================

class TestPropertyReportGeneratorDirect:

    def _gen(self, tmp_path):
        from reports.property.property_generator import PropertyReportGenerator
        return PropertyReportGenerator(output_dir=tmp_path)

    def test_list_available_pages(self, tmp_path):
        """Line 285: list_available_pages."""
        gen = self._gen(tmp_path)
        pages = gen.list_available_pages()
        assert isinstance(pages, list)
        assert "title_overview" in pages

    def test_get_page_categories(self, tmp_path):
        """Line 313: get_page_categories."""
        gen = self._gen(tmp_path)
        cats = gen.get_page_categories()
        assert "property" in cats
        assert "mortgage" in cats

    def test_validate_pages(self, tmp_path):
        """Line 315: validate_pages."""
        gen = self._gen(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "bogus_page"])
        assert "title_overview" in valid
        assert "bogus_page" in invalid

    def test_generate_filename_unknown_id(self, tmp_path):
        """Lines 184-185: missing PropertyID -> 'unknown'."""
        gen = self._gen(tmp_path)
        name = gen._generate_filename({})
        assert "unknown" in name

    def test_auto_select_pages_with_mortgage(self, tmp_path):
        """Line 174-175: rloan_data -> includes mortgage pages."""
        gen = self._gen(tmp_path)
        pages = gen._auto_select_pages(_PROP_DATA, _MORT_DATA)
        assert "mortgage_overview" in pages

    def test_auto_select_pages_without_mortgage(self, tmp_path):
        """Line 174 (else): no rloan_data -> no mortgage pages."""
        gen = self._gen(tmp_path)
        pages = gen._auto_select_pages(_PROP_DATA, None)
        assert "mortgage_overview" not in pages

    def test_generate_elements_skips_unknown(self, tmp_path):
        """Lines 198-199: unknown page -> skip."""
        gen = self._gen(tmp_path)
        elements = gen._generate_elements(["bogus"], property_data=_PROP_DATA, rloan_data=None)
        assert isinstance(elements, list)

    def test_generate_elements_exception_continues(self, tmp_path):
        """Lines 214-216: exception in page -> logged, continue."""
        gen = self._gen(tmp_path)
        bad = MagicMock()
        bad.generate_elements.side_effect = RuntimeError("page crash")
        gen.pages["bad_page"] = bad
        elements = gen._generate_elements(["bad_page", "title_overview"], property_data=_PROP_DATA, rloan_data=None)
        assert isinstance(elements, list)

    def test_generate_property_only_report(self, tmp_path):
        """Lines 251-255: property-only report."""
        gen = self._gen(tmp_path)
        path = gen.generate_property_only_report(_PROP_DATA)
        assert path.exists()

    def test_generate_mortgage_focused_report(self, tmp_path):
        """Lines 257-264: mortgage-focused report."""
        gen = self._gen(tmp_path)
        path = gen.generate_mortgage_focused_report(_PROP_DATA, _MORT_DATA)
        assert path.exists()

    def test_generate_risk_focused_report_with_mortgage(self, tmp_path):
        """Lines 266-276: risk-focused report with mortgage data."""
        gen = self._gen(tmp_path)
        path = gen.generate_risk_focused_report(_PROP_DATA, _MORT_DATA)
        assert path.exists()

    def test_generate_risk_focused_report_no_mortgage(self, tmp_path):
        """Lines 266-276: risk-focused report without mortgage data."""
        gen = self._gen(tmp_path)
        path = gen.generate_risk_focused_report(_PROP_DATA)
        assert path.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        """Lines 69-70: output_dir=None -> uses config.get_property_reports_dir()."""
        from config import config
        prop_dir = tmp_path / "prop_reports"
        monkeypatch.setattr(config, "get_property_reports_dir", lambda: prop_dir)
        from reports.property.property_generator import PropertyReportGenerator
        gen = PropertyReportGenerator()
        assert gen.output_dir == prop_dir


# ===========================================================================
# generate_property_report convenience function
# ===========================================================================

class TestGeneratePropertyReport:
    """Tests for the convenience function generate_property_report."""

    PROP = {"PropertyHeader": {"PropertyID": "PROP-001"}}

    def _mock_gen(self, tmp_path):
        fake_pdf = tmp_path / "prop_report.pdf"
        fake_pdf.write_bytes(b"%PDF")
        mock = MagicMock()
        mock.generate_property_only_report.return_value = fake_pdf
        mock.generate_mortgage_focused_report.return_value = fake_pdf
        mock.generate_risk_focused_report.return_value = fake_pdf
        mock.generate_report.return_value = fake_pdf
        return mock

    def test_property_only_type(self, tmp_path):
        """Line 317-318: 'property-only' -> generate_property_only_report."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(self.PROP, output_dir=tmp_path, report_type="property-only", auto_open=False)
            mock.generate_property_only_report.assert_called_once()

    def test_mortgage_focused_type(self, tmp_path):
        """Lines 319-320: 'mortgage-focused' with rloan_data."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(self.PROP, rloan_data={"m": 1}, output_dir=tmp_path, report_type="mortgage-focused", auto_open=False)
            mock.generate_mortgage_focused_report.assert_called_once()

    def test_risk_focused_type(self, tmp_path):
        """Lines 321-322: 'risk-focused'."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(self.PROP, output_dir=tmp_path, report_type="risk-focused", auto_open=False)
            mock.generate_risk_focused_report.assert_called_once()

    def test_unknown_type_falls_back(self, tmp_path):
        """Lines 323-324: unknown type -> generate_report."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(self.PROP, output_dir=tmp_path, report_type="full", auto_open=False)
            mock.generate_report.assert_called_once()

    def test_auto_open_false_skips(self, tmp_path):
        """Lines 335-336: auto_open=False -> skips opening."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            with patch("reports.property.property_generator.open_pdf_file") as mock_open:
                from reports.property.property_generator import generate_property_report
                generate_property_report(self.PROP, output_dir=tmp_path, report_type="full", auto_open=False)
                mock_open.assert_not_called()

    def test_auto_open_true_tries(self, tmp_path):
        """Lines 327-334: auto_open=True -> calls open_pdf_file."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            with patch("reports.property.property_generator.open_pdf_file", return_value=True) as mock_open:
                from reports.property.property_generator import generate_property_report
                generate_property_report(self.PROP, output_dir=tmp_path, report_type="full", auto_open=True)
                assert mock_open.called

    def test_auto_open_exception_does_not_raise(self, tmp_path):
        """Lines 332-334: open_pdf_file raises -> warning logged, no raise."""
        mock = self._mock_gen(tmp_path)
        with patch("reports.property.property_generator.PropertyReportGenerator", return_value=mock):
            with patch("reports.property.property_generator.open_pdf_file", side_effect=OSError("no viewer")):
                from reports.property.property_generator import generate_property_report
                result = generate_property_report(self.PROP, output_dir=tmp_path, report_type="full", auto_open=True)
                assert result is not None
