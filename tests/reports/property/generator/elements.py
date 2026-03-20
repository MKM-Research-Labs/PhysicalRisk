# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for _generate_elements and _create_header_footer."""

from unittest.mock import MagicMock

from .conftest import make_generator


# ===========================================================================
# TestGenerateElements
# ===========================================================================

class TestGenerateElements:

    def test_returns_list(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview"])
        assert isinstance(elements, list)

    def test_empty_page_list(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen._generate_elements(prop_data, None, []) == []

    def test_unknown_page_skipped(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["totally_bogus_xyz"])
        assert len(elements) == 0

    def test_multiple_pages_have_page_breaks(self, tmp_path, prop_data):
        from reportlab.platypus import PageBreak
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview", "location"])
        assert any(isinstance(e, PageBreak) for e in elements)

    def test_first_page_no_page_break(self, tmp_path, prop_data):
        from reportlab.platypus import PageBreak
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview"])
        assert not any(isinstance(e, PageBreak) for e in elements)

    def test_exception_in_page_module_continues(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        bad = MagicMock()
        bad.generate_elements.side_effect = RuntimeError("page exploded")
        gen.property_pages["_bad"] = bad
        elements = gen._generate_elements(prop_data, None, ["_bad", "title_overview"])
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_mortgage_data_passed_to_page(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        spy = MagicMock(wraps=gen.property_pages["title_overview"])
        gen.property_pages["title_overview"] = spy
        gen._generate_elements(prop_data, mort_data, ["title_overview"])
        spy.generate_elements.assert_called_once_with(prop_data, mort_data)

    def test_mixed_valid_and_unknown_pages(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview", "bogus_page_abc"])
        assert len(elements) > 0


# ===========================================================================
# TestHeaderFooter
# ===========================================================================

class TestHeaderFooter:

    def _mock_doc(self):
        doc = MagicMock()
        doc.height = 700
        doc.topMargin = 80
        doc.bottomMargin = 70
        doc.width = 500
        doc.page = 1
        return doc

    def test_header_footer_callable(self, tmp_path):
        gen = make_generator(tmp_path)
        canvas = MagicMock()
        gen._create_header_footer(canvas, self._mock_doc())
        canvas.saveState.assert_called_once()
        canvas.restoreState.assert_called_once()

    def test_header_footer_draws_confidential(self, tmp_path):
        gen = make_generator(tmp_path)
        canvas = MagicMock()
        gen._create_header_footer(canvas, self._mock_doc())
        assert canvas.drawCentredString.called
