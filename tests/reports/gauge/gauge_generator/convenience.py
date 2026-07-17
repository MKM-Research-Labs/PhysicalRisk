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

"""Tests for generate_gauge_report convenience function, _find_gauge_by_id, and edge cases."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from .conftest import _minimal_gauge, _timeseries_data, _make_generator


def _mock_gauge_generator(tmp_path: Path):
    fake_pdf = tmp_path / "gauge_report_mock.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 mock")
    mock = MagicMock()
    mock.generate_basic_report.return_value = fake_pdf
    mock.generate_monitoring_report.return_value = fake_pdf
    mock.generate_analysis_report.return_value = fake_pdf
    mock.generate_report.return_value = fake_pdf
    return mock, fake_pdf


class TestGenerateGaugeReportModuleFunction:

    GAUGE = _minimal_gauge()

    def test_basic_type_calls_generate_basic(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                  report_type="basic", auto_open=False)
        mock.generate_basic_report.assert_called_once()

    def test_monitoring_type_with_timeseries_calls_monitoring(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        ts = _timeseries_data()
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(self.GAUGE, timeseries_data=ts,
                                  output_dir=tmp_path, report_type="monitoring",
                                  auto_open=False)
        mock.generate_monitoring_report.assert_called_once()

    def test_monitoring_without_timeseries_falls_back(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(self.GAUGE, timeseries_data=None,
                                  output_dir=tmp_path, report_type="monitoring",
                                  auto_open=False)
        mock.generate_report.assert_called_once()

    def test_analysis_type_calls_generate_analysis(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                  report_type="analysis", auto_open=False)
        mock.generate_analysis_report.assert_called_once()

    def test_unknown_type_calls_generate_report(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                  report_type="unknown_type_xyz", auto_open=False)
        mock.generate_report.assert_called_once()

    def test_returns_path(self, tmp_path):
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=False)
        assert result == fake_pdf

    def test_auto_open_true_open_succeeds(self, tmp_path):
        """Lines 343-344: auto_open=True + open_pdf_file succeeds → both lines covered.

        reports.gauge.report_generator doesn't exist yet, so we inject a fake module
        into sys.modules to make 'from .report_generator import open_pdf_file' succeed.
        """
        import sys
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        fake_rg = MagicMock()
        import_patch = {'reports.gauge.report_generator': fake_rg}
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock), \
             patch.dict(sys.modules, import_patch):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=True)
        fake_rg.open_pdf_file.assert_called_once_with(fake_pdf)
        assert result == fake_pdf

    def test_auto_open_true_handles_exception(self, tmp_path):
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=True)
        assert result is not None

    def test_auto_open_false_returns_path(self, tmp_path):
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(self.GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=False)
        assert result == fake_pdf


class TestFindGaugeByIdAdditional:

    def test_flood_gauges_key_first_gauge(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "G-A"}}},
            {"FloodGauge": {"Header": {"GaugeID": "G-B"}}},
        ]}
        result = _find_gauge_by_id(data, "G-A")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-A"

    def test_flood_gauges_key_last_gauge(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            {"FloodGauge": {"Header": {"GaugeID": "G-A"}}},
            {"FloodGauge": {"Header": {"GaugeID": "G-C"}}},
        ]}
        result = _find_gauge_by_id(data, "G-C")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-C"

    def test_malformed_entry_with_none_skipped(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            None,
            {"FloodGauge": {"Header": {"GaugeID": "G-OK"}}},
        ]}
        result = _find_gauge_by_id(data, "G-OK")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-OK"

    def test_malformed_entry_missing_flood_gauge_key_skipped(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            {"some_other_key": {}},
            {"FloodGauge": {"Header": {"GaugeID": "G-REAL"}}},
        ]}
        result = _find_gauge_by_id(data, "G-REAL")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-REAL"

    def test_single_flood_gauge_dict_returns_itself(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"FloodGauge": {"Header": {"GaugeID": "G-SINGLE"}}}
        result = _find_gauge_by_id(data, "G-SINGLE")
        assert result is data

    def test_integer_input_raises(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        with pytest.raises(ValueError):
            _find_gauge_by_id(123, "G-001")

    def test_string_input_raises(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        with pytest.raises(ValueError):
            _find_gauge_by_id("not-a-valid-input", "G-001")

    def test_dict_without_known_key_raises(self):
        """Line 361: dict with neither 'flood_gauges' nor 'FloodGauge' → ValueError."""
        from reports.gauge.gauge_generator import _find_gauge_by_id
        with pytest.raises(ValueError, match="Invalid gauge data structure"):
            _find_gauge_by_id({"unknown_key": []}, "G-001")

    def test_list_input_used_directly(self):
        """Line 363: list input → list used directly as gauge collection."""
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = [{"FloodGauge": {"Header": {"GaugeID": "G-LIST"}}}]
        result = _find_gauge_by_id(data, "G-LIST")
        assert result["FloodGauge"]["Header"]["GaugeID"] == "G-LIST"

    def test_gauge_not_found_raises(self):
        """Line 375: gauge_id not present in any entry → ValueError."""
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "G-A"}}}]}
        with pytest.raises(ValueError, match="G-NOPE not found"):
            _find_gauge_by_id(data, "G-NOPE")


class TestEdgeCases:

    def test_completely_empty_gauge_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_basic_report({})
        assert path.exists()

    def test_none_flood_gauge_header(self, tmp_path):
        gen = _make_generator(tmp_path)
        data = {"FloodGauge": {"Header": None, "SensorDetails": {}, "FloodStage": {}}}
        path = gen.generate_basic_report(data)
        assert path.exists()

    def test_report_with_all_pages(self, tmp_path, gauge_data, ts_data):
        gen = _make_generator(tmp_path)
        all_pages = list(gen.pages.keys())
        path = gen.generate_report(gauge_data, timeseries_data=ts_data,
                                   pages_to_include=all_pages)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_single_page_report(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        assert path.exists()

    def test_gauge_data_with_hazard_curve_and_timeseries(self, tmp_path):
        gen = _make_generator(tmp_path)
        data = _minimal_gauge()
        data["FloodGauge"]["hazard_curve"] = {"annual_hazard_rate_alert": 0.1}
        path = gen.generate_report(data, timeseries_data=_timeseries_data())
        assert path.exists()

    def test_output_is_non_empty_bytes(self, tmp_path, gauge_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(gauge_data, pages_to_include=["title_overview"])
        content = path.read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0
