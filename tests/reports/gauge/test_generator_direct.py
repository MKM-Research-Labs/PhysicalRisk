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

"""
Tests for reports.gauge.gauge_generator — direct GaugeReportGenerator and _find_gauge_by_id.

Covers: page listing, validation, filename generation, auto-select,
element generation, report generation methods, and _find_gauge_by_id utility.
"""

from unittest.mock import patch, MagicMock

import pytest


_GAUGE_DATA = {
    "FloodGauge": {
        "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
        "SensorDetails": {"GaugeInformation": {}, "SensorSpecifications": {}},
        "FloodStage": {"UK": {}},
        "SensorStats": {},
    }
}


class TestGaugeReportGeneratorDirect:

    def _gen(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        return GaugeReportGenerator(output_dir=tmp_path)

    def test_list_available_pages(self, tmp_path):
        """Line 279: list_available_pages returns list of strings."""
        gen = self._gen(tmp_path)
        pages = gen.list_available_pages()
        assert isinstance(pages, list)
        assert "title_overview" in pages

    def test_get_page_categories(self, tmp_path):
        """Line 313: get_page_categories returns dict."""
        gen = self._gen(tmp_path)
        cats = gen.get_page_categories()
        assert isinstance(cats, dict)
        assert "gauge_info" in cats

    def test_validate_pages_valid(self, tmp_path):
        """Line 315: validate_pages with all valid pages."""
        gen = self._gen(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "sensor_details"])
        assert "title_overview" in valid
        assert invalid == []

    def test_validate_pages_with_invalid(self, tmp_path):
        """validate_pages with some invalid page names."""
        gen = self._gen(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "nonexistent_page"])
        assert "title_overview" in valid
        assert "nonexistent_page" in invalid

    def test_generate_filename_no_gauge_id(self, tmp_path):
        """Lines 176-177: missing GaugeID -> uses 'unknown' in filename."""
        gen = self._gen(tmp_path)
        name = gen._generate_filename({})
        assert "unknown" in name
        assert name.endswith(".pdf")

    def test_generate_filename_with_gauge_id(self, tmp_path):
        """Line 175: gauge_id extracted for filename."""
        gen = self._gen(tmp_path)
        name = gen._generate_filename(_GAUGE_DATA)
        assert "GAUGE-001" in name

    def test_auto_select_pages_no_analysis_data(self, tmp_path):
        """Line 163 (else branch): no timeseries or hazard -> no analysis pages."""
        gen = self._gen(tmp_path)
        pages = gen._auto_select_pages({}, None)
        analysis_pages = ["risk_assessment", "flood_history"]
        assert not any(p in pages for p in analysis_pages)

    def test_auto_select_pages_with_hazard(self, tmp_path):
        """Line 163 (if branch): gauge_data.get('hazard_curve') -> include analysis."""
        gen = self._gen(tmp_path)
        gauge_with_hc = {"hazard_curve": {"annual_hazard_rate_alert": 0.1}}
        pages = gen._auto_select_pages(gauge_with_hc, None)
        assert "risk_assessment" in pages

    def test_generate_elements_skips_unknown_page(self, tmp_path):
        """Lines 190-191: unknown page -> warning logged, skipped."""
        gen = self._gen(tmp_path)
        elements = gen._generate_elements(["nonexistent_page"], gauge_data=_GAUGE_DATA, timeseries_data=None)
        assert isinstance(elements, list)

    def test_generate_monitoring_report(self, tmp_path):
        """Lines 261-263: generate_monitoring_report creates PDF."""
        gen = self._gen(tmp_path)
        path = gen.generate_monitoring_report(_GAUGE_DATA, None)
        assert path.exists()

    def test_generate_analysis_report(self, tmp_path):
        """Lines 269-270: generate_analysis_report creates PDF."""
        gen = self._gen(tmp_path)
        path = gen.generate_analysis_report(_GAUGE_DATA)
        assert path.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        """Lines 59-60: output_dir=None -> uses config.get_gauge_reports_dir()."""
        from config import config
        gauge_dir = tmp_path / "gauge_reports"
        monkeypatch.setattr(config, "get_gauge_reports_dir", lambda: gauge_dir)
        from reports.gauge.gauge_generator import GaugeReportGenerator
        gen = GaugeReportGenerator()
        assert gen.output_dir == gauge_dir

    def test_generate_elements_exception_continues(self, tmp_path):
        """Lines 208-210: exception in page -> logged, continue to next page."""
        gen = self._gen(tmp_path)
        bad_page = MagicMock()
        bad_page.generate_elements.side_effect = RuntimeError("page error")
        gen.pages["bad_page"] = bad_page
        # Should not raise, just skip bad page
        elements = gen._generate_elements(["bad_page", "title_overview"], gauge_data=_GAUGE_DATA, timeseries_data=None)
        assert isinstance(elements, list)


class TestFindGaugeById:
    """Tests for _find_gauge_by_id utility (lines 332-356)."""

    def test_single_gauge_dict_returns_self(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}
        result = _find_gauge_by_id(data, "GAUGE-001")
        assert result is data

    def test_flood_gauges_key_found(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-002"}}}]}
        result = _find_gauge_by_id(data, "GAUGE-002")
        assert result == data["flood_gauges"][0]

    def test_list_input_found(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        gauges = [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-003"}}}]
        result = _find_gauge_by_id(gauges, "GAUGE-003")
        assert result == gauges[0]

    def test_not_found_raises_value_error(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [{"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}]}
        with pytest.raises(ValueError, match="GAUGE-999"):
            _find_gauge_by_id(data, "GAUGE-999")

    def test_invalid_dict_structure_raises(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"some_other_key": []}
        with pytest.raises(ValueError):
            _find_gauge_by_id(data, "GAUGE-001")

    def test_invalid_type_raises(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        with pytest.raises(ValueError):
            _find_gauge_by_id(42, "GAUGE-001")

    def test_malformed_gauge_entry_skipped(self):
        from reports.gauge.gauge_generator import _find_gauge_by_id
        data = {"flood_gauges": [
            None,  # malformed
            {"FloodGauge": {"Header": {"GaugeID": "GAUGE-004"}}},
        ]}
        result = _find_gauge_by_id(data, "GAUGE-004")
        assert result == data["flood_gauges"][1]


class TestGaugeGeneratorDirectCalls:
    """Cover lines in gauge_generator.py not hit by mocked tests."""

    _GAUGE = {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
            "SensorDetails": {"GaugeInformation": {}, "SensorSpecifications": {}},
            "FloodStage": {"UK": {}},
            "SensorStats": {},
        }
    }

    def _gen(self, tmp_path):
        from reports.gauge.gauge_generator import GaugeReportGenerator
        return GaugeReportGenerator(output_dir=tmp_path)

    def test_generate_basic_report_direct(self, tmp_path):
        """Lines 251-254: generate_basic_report() body on real generator."""
        gen = self._gen(tmp_path)
        path = gen.generate_basic_report(self._GAUGE)
        assert path.exists()
        assert path.suffix == ".pdf"

    def test_generate_report_no_pages_uses_auto_select(self, tmp_path):
        """Line 119: generate_report(pages_to_include=None) calls _auto_select_pages."""
        gen = self._gen(tmp_path)
        path = gen.generate_report(self._GAUGE, None, pages_to_include=None)
        assert path.exists()

    def test_generate_gauge_report_fn_basic(self, tmp_path):
        """Lines 307-311: generate_gauge_report() in gauge_generator.py, basic type."""
        from reports.gauge.gauge_generator import generate_gauge_report
        path = generate_gauge_report(self._GAUGE, output_dir=tmp_path,
                                     report_type='basic', auto_open=False)
        assert path.exists()

    def test_generate_gauge_report_fn_monitoring(self, tmp_path):
        """Line 313: monitoring branch in gauge_generator.generate_gauge_report."""
        from reports.gauge.gauge_generator import generate_gauge_report
        path = generate_gauge_report(self._GAUGE, timeseries_data={"readings": []},
                                     output_dir=tmp_path, report_type='monitoring',
                                     auto_open=False)
        assert path.exists()

    def test_generate_gauge_report_fn_analysis(self, tmp_path):
        """Line 315: analysis branch in gauge_generator.generate_gauge_report."""
        from reports.gauge.gauge_generator import generate_gauge_report
        path = generate_gauge_report(self._GAUGE, output_dir=tmp_path,
                                     report_type='analysis', auto_open=False)
        assert path.exists()

    def test_generate_gauge_report_fn_fallback(self, tmp_path):
        """Lines 316-317: unknown type falls back to generate_report."""
        from reports.gauge.gauge_generator import generate_gauge_report
        path = generate_gauge_report(self._GAUGE, output_dir=tmp_path,
                                     report_type='unknown', auto_open=False)
        assert path.exists()

    def test_generate_gauge_report_fn_auto_open_true(self, tmp_path):
        """Lines 321-328: auto_open=True — open attempt caught, does not raise."""
        from reports.gauge.gauge_generator import generate_gauge_report
        # In test environment the PDF viewer will fail -> hits the except block
        path = generate_gauge_report(self._GAUGE, output_dir=tmp_path,
                                     report_type='basic', auto_open=True)
        assert path.exists()

    def test_init_auto_open_returns_false(self, tmp_path):
        """Lines 102-103 in __init__.py: auto_open=True, open returns False."""
        from reports.gauge import generate_gauge_report
        from reports.gauge.gauge_generator import GaugeReportGenerator as RealGen
        real_gen = RealGen(output_dir=tmp_path)
        real_gen.generate_basic_report(self._GAUGE)  # pre-generate so mock can return path
        fake_pdf = tmp_path / "gauge_report.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4")
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator") as MockGen:
            mock_instance = MockGen.return_value
            mock_instance.generate_basic_report.return_value = fake_pdf
            with patch("reports.utils.open_pdf.open_pdf_file", return_value=False):
                result = generate_gauge_report(self._GAUGE, output_dir=tmp_path,
                                               report_type='basic', auto_open=True)
        assert result == fake_pdf
