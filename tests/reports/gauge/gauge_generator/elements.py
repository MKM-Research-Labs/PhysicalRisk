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

"""Tests for GaugeReportGenerator._generate_elements and generate_report."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from .conftest import _make_generator


class TestGenerateElements:

    def test_returns_list(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(["title_overview"], gauge_data=gauge_data, timeseries_data=None)
        assert isinstance(elements, list)

    def test_empty_page_list_returns_empty(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements([], gauge_data=gauge_data, timeseries_data=None)
        assert elements == []

    def test_unknown_page_skipped(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(["totally_bogus_xyz"], gauge_data=gauge_data, timeseries_data=None)
        assert len(elements) == 0

    def test_first_page_no_page_break(self, tmp_path, gauge_data):
        from reportlab.platypus import PageBreak
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(["title_overview"], gauge_data=gauge_data, timeseries_data=None)
        assert not any(isinstance(e, PageBreak) for e in elements)

    def test_multiple_pages_have_page_break(self, tmp_path, gauge_data):
        from reportlab.platypus import PageBreak
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(["title_overview", "sensor_details"], gauge_data=gauge_data, timeseries_data=None)
        assert any(isinstance(e, PageBreak) for e in elements)

    def test_exception_in_page_continues(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        bad = MagicMock()
        bad.generate_elements.side_effect = RuntimeError("exploded")
        gen.pages["_bad"] = bad
        elements = gen._generate_elements(["_bad", "title_overview"], gauge_data=gauge_data, timeseries_data=None)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_timeseries_passed_to_page(self, tmp_path, gauge_data, ts_data):
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["title_overview"])
        gen.pages["title_overview"] = spy
        gen._generate_elements(["title_overview"], gauge_data=gauge_data, timeseries_data=ts_data)
        spy.generate_elements.assert_called_once_with(gauge_data=gauge_data, timeseries_data=ts_data)

    def test_none_timeseries_passed_to_page(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["title_overview"])
        gen.pages["title_overview"] = spy
        gen._generate_elements(["title_overview"], gauge_data=gauge_data, timeseries_data=None)
        spy.generate_elements.assert_called_once_with(gauge_data=gauge_data, timeseries_data=None)

    def test_mixed_valid_and_unknown_pages(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        elements = gen._generate_elements(["title_overview", "bogus_page"], gauge_data=gauge_data, timeseries_data=None)
        assert len(elements) > 0


class TestGenerateReport:

    def test_returns_path(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        result = gen.generate_report(gauge_data)
        assert isinstance(result, Path)

    def test_pdf_exists(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_report(gauge_data).exists()

    def test_pdf_non_empty(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data)
        assert path.stat().st_size > 0

    def test_pdf_suffix(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        assert gen.generate_report(gauge_data).suffix == ".pdf"

    def test_custom_output_filename(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, output_filename="my_gauge.pdf")
        assert path.name == "my_gauge.pdf"
        assert path.exists()

    def test_custom_pages_to_include(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview", "data_summary"])
        assert path.exists()

    def test_with_timeseries_data(self, tmp_path, gauge_data, ts_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, timeseries_data=ts_data)
        assert path.exists()

    def test_auto_select_called_when_pages_none(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(gauge_data, pages_to_include=None)
        spy.assert_called_once()

    def test_auto_select_not_called_when_pages_provided(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        spy.assert_not_called()

    def test_empty_gauge_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_report({})
        assert path.exists()

    def test_all_unknown_pages_still_creates_pdf(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["xxx", "yyy"])
        assert path.exists()

    def test_pdf_is_bytes(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        content = path.read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0
