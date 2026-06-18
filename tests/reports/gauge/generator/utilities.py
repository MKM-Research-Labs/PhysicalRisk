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

"""Tests for list_available_pages, get_page_categories, validate_pages, and header/footer."""

from unittest.mock import MagicMock

from .conftest import make_generator


class TestUtilityMethods:

    def test_list_available_pages_returns_list(self, tmp_path):
        gen = make_generator(tmp_path)
        pages = gen.list_available_pages()
        assert isinstance(pages, list)

    def test_list_available_pages_contains_expected(self, tmp_path):
        gen = make_generator(tmp_path)
        pages = gen.list_available_pages()
        expected = {"title_overview", "sensor_details", "location", "data_summary"}
        assert expected <= set(pages)

    def test_list_available_pages_non_empty(self, tmp_path):
        gen = make_generator(tmp_path)
        assert len(gen.list_available_pages()) > 0

    def test_get_page_categories_returns_dict(self, tmp_path):
        gen = make_generator(tmp_path)
        cats = gen.get_page_categories()
        assert isinstance(cats, dict)

    def test_get_page_categories_contains_expected_keys(self, tmp_path):
        gen = make_generator(tmp_path)
        cats = gen.get_page_categories()
        for key in ("gauge_info", "operational", "analysis", "summary"):
            assert key in cats

    def test_get_page_categories_returns_copy(self, tmp_path):
        gen = make_generator(tmp_path)
        cats = gen.get_page_categories()
        cats["__new_key__"] = []
        assert "__new_key__" not in gen.categories

    def test_validate_pages_all_valid(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "sensor_details"])
        assert "title_overview" in valid
        assert "sensor_details" in valid
        assert invalid == []

    def test_validate_pages_all_invalid(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["bogus_one", "bogus_two"])
        assert valid == []
        assert "bogus_one" in invalid
        assert "bogus_two" in invalid

    def test_validate_pages_mixed(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "nonexistent_page"])
        assert "title_overview" in valid
        assert "nonexistent_page" in invalid

    def test_validate_pages_empty_list(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages([])
        assert valid == []
        assert invalid == []


class TestHeaderFooter:

    def test_header_footer_callable(self, tmp_path):
        gen = make_generator(tmp_path)
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

    def test_header_footer_draws_header_strings(self, tmp_path):
        gen = make_generator(tmp_path)
        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.height = 700
        mock_doc.topMargin = 80
        mock_doc.bottomMargin = 70
        mock_doc.width = 500
        gen._create_header_footer(mock_canvas, mock_doc)
        assert mock_canvas.drawString.call_count >= 1
        assert mock_canvas.drawRightString.call_count >= 2

    def test_header_footer_draws_confidential_footer(self, tmp_path):
        gen = make_generator(tmp_path)
        mock_canvas = MagicMock()
        mock_doc = MagicMock()
        mock_doc.height = 700
        mock_doc.topMargin = 80
        mock_doc.bottomMargin = 70
        mock_doc.width = 500
        gen._create_header_footer(mock_canvas, mock_doc)
        assert mock_canvas.drawCentredString.called
