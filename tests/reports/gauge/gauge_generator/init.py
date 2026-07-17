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

"""Tests for GaugeReportGenerator.__init__, _auto_select_pages, _generate_filename."""

from pathlib import Path

from .conftest import _make_generator


class TestGaugeReportGeneratorInit:

    def test_explicit_output_dir_string(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator(output_dir=str(tmp_path))
        assert gen.output_dir == tmp_path

    def test_explicit_output_dir_path(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator(output_dir=tmp_path)
        assert isinstance(gen.output_dir, Path)

    def test_output_dir_created(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        new_dir = tmp_path / "brand_new_dir"
        GaugeReportGenerator(output_dir=new_dir)
        assert new_dir.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        from config import config
        gauge_dir = tmp_path / "gauge_reports"
        monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: gauge_dir)
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator()
        assert gen.output_dir == gauge_dir

    def test_pages_dict_initialized(self, tmp_path):
        gen = _make_generator(tmp_path)
        expected = {
            "title_overview", "sensor_details", "location",
            "measurements", "flood_stages",
            "risk_assessment", "data_summary", "flood_history",
            "hazard_curves", "prs_pricing", "current_risk", "trading",
        }
        assert expected <= set(gen.pages.keys())

    def test_categories_dict_initialized(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert "gauge_info" in gen.categories
        assert "operational" in gen.categories
        assert "analysis" in gen.categories
        assert "summary" in gen.categories


class TestAutoSelectPages:

    def test_returns_list(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        assert isinstance(pages, list)
        assert len(pages) > 0

    def test_all_pages_exist(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        for p in pages:
            assert p in gen.pages

    def test_without_timeseries_or_hazard_no_analysis_pages(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages({}, None)
        analysis_pages = gen.categories["analysis"]
        assert not any(p in pages for p in analysis_pages)

    def test_with_timeseries_includes_analysis_pages(self, tmp_path, gauge_data, ts_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, ts_data)
        analysis_pages = gen.categories["analysis"]
        assert any(p in pages for p in analysis_pages)

    def test_with_hazard_curve_includes_analysis_pages(self, tmp_path):
        gen = _make_generator(tmp_path)
        gauge_with_hc = {"hazard_curve": {"annual_hazard_rate_alert": 0.05}}
        pages = gen._auto_select_pages(gauge_with_hc, None)
        analysis_pages = gen.categories["analysis"]
        assert any(p in pages for p in analysis_pages)

    def test_always_includes_summary_pages(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages({}, None)
        for sp in gen.categories["summary"]:
            assert sp in pages

    def test_always_includes_gauge_info_pages(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        for gp in gen.categories["gauge_info"]:
            assert gp in pages

    def test_always_includes_operational_pages(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(gauge_data, None)
        for op in gen.categories["operational"]:
            assert op in pages


class TestGenerateFilename:

    def test_returns_string(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename(gauge_data)
        assert isinstance(name, str)

    def test_ends_with_pdf(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        assert gen._generate_filename(gauge_data).endswith(".pdf")

    def test_contains_gauge_id(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename(gauge_data)
        assert "GAUGE-001" in name

    def test_missing_gauge_id_uses_unknown(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename({})
        assert "unknown" in name
        assert name.endswith(".pdf")

    def test_partial_path_missing_header(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename({"FloodGauge": {}})
        assert "unknown" in name

    def test_partial_path_missing_gauge_id(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename({"FloodGauge": {"Header": {}}})
        assert "unknown" in name

    def test_timestamp_in_filename(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename(gauge_data)
        digits = sum(c.isdigit() for c in name)
        assert digits >= 8
