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

"""Tests for PropertyReportGenerator._generate_elements and generate_report."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from .conftest import _make_generator


class TestGenerateElements:

    def test_returns_list(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview"])
        assert isinstance(elements, list)

    def test_empty_page_list(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, [])
        assert elements == []

    def test_unknown_page_skipped(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["totally_bogus_xyz"])
        assert len(elements) == 0

    def test_multiple_pages_have_page_breaks(self, tmp_path, prop_data):
        from reportlab.platypus import PageBreak
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview", "location"])
        assert any(isinstance(e, PageBreak) for e in elements)

    def test_first_page_no_page_break(self, tmp_path, prop_data):
        from reportlab.platypus import PageBreak
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview"])
        assert not any(isinstance(e, PageBreak) for e in elements)

    def test_exception_in_page_module_continues(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        bad = MagicMock()
        bad.generate_elements.side_effect = RuntimeError("page exploded")
        gen.property_pages["_bad"] = bad
        elements = gen._generate_elements(prop_data, None, ["_bad", "title_overview"])
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_mortgage_data_passed_to_page(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.property_pages["title_overview"])
        gen.property_pages["title_overview"] = spy
        gen._generate_elements(prop_data, mort_data, ["title_overview"])
        spy.generate_elements.assert_called_once_with(prop_data, mort_data)

    def test_mixed_valid_and_unknown_pages(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(prop_data, None, ["title_overview", "bogus_page_abc"])
        assert len(elements) > 0


class TestGenerateReport:

    def test_returns_path(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        result = gen.generate_report(prop_data)
        assert isinstance(result, Path)

    def test_pdf_exists(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_report(prop_data).exists()

    def test_pdf_non_empty(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(prop_data)
        assert path.stat().st_size > 0

    def test_pdf_suffix(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_report(prop_data).suffix == ".pdf"

    def test_custom_output_filename(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(prop_data, output_filename="my_prop.pdf")
        assert path.name == "my_prop.pdf"
        assert path.exists()

    def test_custom_pages_to_include(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(prop_data, pages_to_include=["title_overview", "data_summary"])
        assert path.exists()

    def test_with_mortgage_data(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(prop_data, mortgage_data=mort_data)
        assert path.exists()

    def test_auto_select_called_when_pages_none(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(prop_data, pages_to_include=None)
        spy.assert_called_once()

    def test_auto_select_not_called_when_pages_provided(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(prop_data, pages_to_include=["title_overview"])
        spy.assert_not_called()

    def test_empty_property_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_report({})
        assert path.exists()

    def test_full_data_report(self, tmp_path, full_prop_data, mort_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(full_prop_data, mortgage_data=mort_data)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_all_unknown_pages_still_creates_pdf(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(prop_data, pages_to_include=["xxx", "yyy"])
        assert path.exists()
