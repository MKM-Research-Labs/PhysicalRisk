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

"""Tests for GaugeReportGenerator._generate_elements and _generate_filename."""

from unittest.mock import MagicMock

from .conftest import make_generator


class TestGenerateFilename:

    def test_returns_string(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        name = gen._generate_filename(gauge_data)
        assert isinstance(name, str)

    def test_ends_with_pdf(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        assert gen._generate_filename(gauge_data).endswith(".pdf")

    def test_contains_gauge_id(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        name = gen._generate_filename(gauge_data)
        assert "GAUGE-001" in name

    def test_missing_gauge_id_uses_unknown(self, tmp_path):
        gen = make_generator(tmp_path)
        name = gen._generate_filename({})
        assert "unknown" in name
        assert name.endswith(".pdf")

    def test_partial_path_missing_header(self, tmp_path):
        gen = make_generator(tmp_path)
        name = gen._generate_filename({"FloodGauge": {}})
        assert "unknown" in name

    def test_partial_path_missing_gauge_id(self, tmp_path):
        gen = make_generator(tmp_path)
        name = gen._generate_filename({"FloodGauge": {"Header": {}}})
        assert "unknown" in name

    def test_timestamp_in_filename(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        name = gen._generate_filename(gauge_data)
        digits = sum(c.isdigit() for c in name)
        assert digits >= 8


class TestGenerateElements:

    def test_returns_list(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(gauge_data, None, ["title_overview"])
        assert isinstance(elements, list)

    def test_empty_page_list_returns_empty(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(gauge_data, None, [])
        assert elements == []

    def test_unknown_page_skipped(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(gauge_data, None, ["totally_bogus_xyz"])
        assert len(elements) == 0

    def test_first_page_no_page_break(self, tmp_path, gauge_data):
        from reportlab.platypus import PageBreak
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(gauge_data, None, ["title_overview"])
        assert not any(isinstance(e, PageBreak) for e in elements)

    def test_multiple_pages_have_page_break(self, tmp_path, gauge_data):
        from reportlab.platypus import PageBreak
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(gauge_data, None, ["title_overview", "sensor_details"])
        assert any(isinstance(e, PageBreak) for e in elements)

    def test_exception_in_page_continues(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        bad = MagicMock()
        bad.generate_elements.side_effect = RuntimeError("exploded")
        gen.pages["_bad"] = bad
        elements = gen._generate_elements(gauge_data, None, ["_bad", "title_overview"])
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_timeseries_passed_to_page(self, tmp_path, gauge_data, ts_data):
        gen = make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["title_overview"])
        gen.pages["title_overview"] = spy
        gen._generate_elements(gauge_data, ts_data, ["title_overview"])
        spy.generate_elements.assert_called_once_with(gauge_data, ts_data)

    def test_none_timeseries_passed_to_page(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["title_overview"])
        gen.pages["title_overview"] = spy
        gen._generate_elements(gauge_data, None, ["title_overview"])
        spy.generate_elements.assert_called_once_with(gauge_data, None)

    def test_mixed_valid_and_unknown_pages(self, tmp_path, gauge_data):
        gen = make_generator(tmp_path)
        elements = gen._generate_elements(gauge_data, None, ["title_overview", "bogus_page"])
        assert len(elements) > 0
