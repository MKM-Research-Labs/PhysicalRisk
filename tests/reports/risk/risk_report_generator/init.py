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

"""Tests for RiskReportGenerator.__init__, _auto_select_pages and _generate_filename."""

from pathlib import Path
import pytest
from .conftest import _make_generator


class TestRiskReportGeneratorInit:
    """Tests for __init__ including output-dir resolution."""

    def test_explicit_output_dir_string(self, tmp_path):
        from reports.risk.generator import RiskReportGenerator
        gen = RiskReportGenerator(output_dir=str(tmp_path))
        assert gen.output_dir == tmp_path

    def test_explicit_output_dir_path(self, tmp_path):
        from reports.risk.generator import RiskReportGenerator
        gen = RiskReportGenerator(output_dir=tmp_path)
        assert isinstance(gen.output_dir, Path)

    def test_output_dir_created(self, tmp_path):
        from reports.risk.generator import RiskReportGenerator
        new_dir = tmp_path / "brand_new_dir"
        RiskReportGenerator(output_dir=new_dir)
        assert new_dir.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        """output_dir=None → falls back to config.get_reports_dir('risk')."""
        from config import config
        risk_dir = tmp_path / "risk_reports"
        monkeypatch.setattr(config, "get_reports_dir", lambda _section: risk_dir)
        from reports.risk.generator import RiskReportGenerator
        gen = RiskReportGenerator()
        assert gen.output_dir == risk_dir

    def test_pages_dict_initialized(self, tmp_path):
        gen = _make_generator(tmp_path)
        expected = {
            "title", "executive_summary", "portfolio_overview",
            "risk_analysis", "mortgage_analysis", "property_details", "appendix",
        }
        assert expected <= set(gen.pages.keys())

    def test_categories_dict_initialized(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert "overview" in gen.categories
        assert "analysis" in gen.categories
        assert "appendix" in gen.categories


class TestAutoSelectPages:
    """Tests for _auto_select_pages."""

    def test_returns_list(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(minimal_flood_data)
        assert isinstance(pages, list)
        assert len(pages) > 0

    def test_all_pages_exist(self, tmp_path, full_flood_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(full_flood_data)
        for p in pages:
            assert p in gen.pages

    def test_always_includes_appendix(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(minimal_flood_data)
        assert "appendix" in pages

    def test_includes_overview_pages(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(minimal_flood_data)
        for p in gen.categories["overview"]:
            assert p in pages

    def test_includes_analysis_pages(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(minimal_flood_data)
        for p in gen.categories["analysis"]:
            assert p in pages

    def test_empty_flood_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages({})
        assert isinstance(pages, list)


class TestGenerateFilename:
    """Tests for _generate_filename."""

    def test_returns_string(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename()
        assert isinstance(name, str)

    def test_ends_with_pdf(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert gen._generate_filename().endswith(".pdf")

    def test_contains_flood_risk_report(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert "flood_risk_report" in gen._generate_filename()

    def test_contains_timestamp(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename()
        digits = sum(c.isdigit() for c in name)
        assert digits >= 8

    def test_two_calls_produce_string_names(self, tmp_path):
        import time
        gen = _make_generator(tmp_path)
        n1 = gen._generate_filename()
        time.sleep(1.1)
        n2 = gen._generate_filename()
        assert isinstance(n1, str) and isinstance(n2, str)
