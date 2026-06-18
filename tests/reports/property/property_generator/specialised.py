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

"""Tests for specialised report methods, utility methods, and header/footer."""

from unittest.mock import MagicMock

from .conftest import _make_generator


class TestSpecialisedReportMethods:

    def test_generate_property_only_report_exists(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_property_only_report(prop_data).exists()

    def test_generate_property_only_report_custom_filename(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_property_only_report(prop_data, output_filename="prop_only.pdf")
        assert path.name == "prop_only.pdf"

    def test_generate_mortgage_focused_report_exists(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_mortgage_focused_report(prop_data, mort_data).exists()

    def test_generate_mortgage_focused_report_custom_filename(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_mortgage_focused_report(
            prop_data, mort_data, output_filename="mort_focused.pdf"
        )
        assert path.name == "mort_focused.pdf"

    def test_generate_risk_focused_report_with_mortgage(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_risk_focused_report(prop_data, mort_data)
        assert path.exists()

    def test_generate_risk_focused_report_without_mortgage(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_risk_focused_report(prop_data)
        assert path.exists()

    def test_generate_risk_focused_report_custom_filename(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_risk_focused_report(prop_data, output_filename="risk_only.pdf")
        assert path.name == "risk_only.pdf"

    def test_mortgage_focused_includes_mortgage_context_pages(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["mortgage_overview"])
        gen.pages["mortgage_overview"] = spy
        gen.generate_mortgage_focused_report(prop_data, mort_data)
        spy.generate_elements.assert_called_once()

    def test_risk_focused_with_mortgage_includes_current_status(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["current_status"])
        gen.pages["current_status"] = spy
        gen.generate_risk_focused_report(prop_data, mort_data)
        spy.generate_elements.assert_called_once()

    def test_risk_focused_without_mortgage_excludes_current_status(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["current_status"])
        gen.pages["current_status"] = spy
        gen.generate_risk_focused_report(prop_data)
        spy.generate_elements.assert_not_called()


class TestUtilityMethods:

    def test_list_available_pages_returns_list(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen.list_available_pages()
        assert isinstance(pages, list)

    def test_list_available_pages_contains_all_expected(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen.list_available_pages()
        expected = {
            "title_overview", "location", "attributes", "construction",
            "risk_assessment", "financial", "protection", "history", "transactions",
            "mortgage_overview", "mortgage_details", "mortgage_costs",
            "regulatory", "current_status", "borrower_profile",
            "risk_analysis", "data_summary",
        }
        assert expected <= set(pages)

    def test_get_page_categories_returns_dict(self, tmp_path):
        gen = _make_generator(tmp_path)
        cats = gen.get_page_categories()
        assert isinstance(cats, dict)

    def test_get_page_categories_returns_copy(self, tmp_path):
        gen = _make_generator(tmp_path)
        cats = gen.get_page_categories()
        cats["__new_key__"] = []
        assert "__new_key__" not in gen.categories

    def test_validate_pages_all_valid(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "data_summary"])
        assert "title_overview" in valid
        assert "data_summary" in valid
        assert invalid == []

    def test_validate_pages_all_invalid(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["no_such_page", "another_bogus"])
        assert valid == []
        assert "no_such_page" in invalid
        assert "another_bogus" in invalid

    def test_validate_pages_mixed(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "nonexistent_page"])
        assert "title_overview" in valid
        assert "nonexistent_page" in invalid

    def test_validate_pages_empty_list(self, tmp_path):
        gen = _make_generator(tmp_path)
        valid, invalid = gen.validate_pages([])
        assert valid == []
        assert invalid == []


class TestHeaderFooter:

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

    def test_header_footer_draws_confidential(self, tmp_path):
        gen = _make_generator(tmp_path)
        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.height = 700
        mock_doc.topMargin = 80
        mock_doc.bottomMargin = 70
        mock_doc.width = 500
        gen._create_header_footer(mock_canvas, mock_doc)
        assert mock_canvas.drawCentredString.called
