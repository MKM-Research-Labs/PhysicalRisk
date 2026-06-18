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

"""Tests for specialised report methods, utility methods and header/footer."""

from unittest.mock import MagicMock
import pytest
from .conftest import _make_generator


class TestSpecialisedReportMethods:
    """Tests for generate_basic/detailed/summary/analysis_report."""

    def test_generate_basic_report_exists(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_basic_report(minimal_flood_data).exists()

    def test_generate_basic_report_non_empty(self, tmp_path, full_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_basic_report(full_flood_data)
        assert path.stat().st_size > 0

    def test_generate_detailed_report_exists(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_detailed_report(minimal_flood_data).exists()

    def test_generate_detailed_report_includes_mortgage_page(self, tmp_path, full_flood_data):
        """Detailed report includes mortgage_analysis — verify call reaches that page."""
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["mortgage_analysis"])
        gen.pages["mortgage_analysis"] = spy
        gen.generate_detailed_report(full_flood_data)
        spy.generate_elements.assert_called_once()

    def test_generate_summary_report_exists(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_summary_report(minimal_flood_data).exists()

    def test_generate_summary_report_custom_filename(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_summary_report(minimal_flood_data, output_filename="summary.pdf")
        assert path.name == "summary.pdf"

    def test_generate_analysis_report_exists(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_analysis_report(minimal_flood_data).exists()

    def test_generate_analysis_report_custom_filename(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_analysis_report(minimal_flood_data, output_filename="analysis.pdf")
        assert path.name == "analysis.pdf"

    def test_basic_vs_detailed_page_counts(self, tmp_path, full_flood_data):
        """Detailed report uses more pages than basic, so should produce larger file."""
        gen = _make_generator(tmp_path)
        basic = gen.generate_basic_report(full_flood_data)
        detailed = gen.generate_detailed_report(full_flood_data)
        assert detailed.stat().st_size >= basic.stat().st_size


class TestUtilityMethods:
    """Tests for list_available_pages, get_page_categories, validate_pages."""

    def test_list_available_pages_returns_list(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen.list_available_pages()
        assert isinstance(pages, list)

    def test_list_available_pages_contains_all_expected(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen.list_available_pages()
        expected = {
            "title", "executive_summary", "portfolio_overview",
            "risk_analysis", "mortgage_analysis", "property_details", "appendix",
        }
        assert expected <= set(pages)

    def test_list_available_pages_non_empty(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert len(gen.list_available_pages()) > 0

    def test_get_page_categories_returns_dict(self, tmp_path):
        gen = _make_generator(tmp_path)
        cats = gen.get_page_categories()
        assert isinstance(cats, dict)

    def test_get_page_categories_contains_expected_keys(self, tmp_path):
        gen = _make_generator(tmp_path)
        cats = gen.get_page_categories()
        for key in ("overview", "analysis", "appendix"):
            assert key in cats

    def test_get_page_categories_returns_copy(self, tmp_path):
        """Mutating the returned dict must not affect the generator's internal state."""
        gen = _make_generator(tmp_path)
        cats = gen.get_page_categories()
        cats["__new_key__"] = []
        assert "__new_key__" not in gen.categories

    def test_validate_pages_all_valid(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title", "appendix"])
        assert "title" in valid
        assert "appendix" in valid
        assert invalid == []

    def test_validate_pages_all_invalid(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["bogus_one", "bogus_two"])
        assert valid == []
        assert "bogus_one" in invalid
        assert "bogus_two" in invalid

    def test_validate_pages_mixed(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title", "nonexistent_page"])
        assert "title" in valid
        assert "nonexistent_page" in invalid

    def test_validate_pages_empty_list(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages([])
        assert valid == []
        assert invalid == []


class TestHeaderFooter:
    """Tests for _create_header_footer — ensures it runs without raising."""

    def test_header_footer_callable(self, tmp_path):
        gen = _make_generator(tmp_path)
        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.height = 700
        mock_doc.topMargin = 80
        mock_doc.bottomMargin = 70
        mock_doc.width = 500
        mock_doc.page = 1
        gen._create_header_footer(mock_canvas, mock_doc)
        mock_canvas.saveState.assert_called_once()
        mock_canvas.restoreState.assert_called_once()

    def test_header_footer_draws_strings(self, tmp_path):
        gen = _make_generator(tmp_path)
        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.height = 700
        mock_doc.topMargin = 80
        mock_doc.bottomMargin = 70
        mock_doc.width = 500
        mock_doc.page = 2
        gen._create_header_footer(mock_canvas, mock_doc)
        assert mock_canvas.drawString.call_count >= 1
        assert mock_canvas.drawRightString.call_count >= 2
