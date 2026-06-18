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

"""Tests for the generate_gauge_report module-level convenience function."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from .conftest import make_generator, minimal_gauge, timeseries_data


def _mock_gauge_generator(tmp_path: Path):
    fake_pdf = tmp_path / "gauge_report_mock.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 mock")
    mock = MagicMock()
    mock.generate_basic_report.return_value = fake_pdf
    mock.generate_monitoring_report.return_value = fake_pdf
    mock.generate_analysis_report.return_value = fake_pdf
    mock.generate_report.return_value = fake_pdf
    return mock, fake_pdf


GAUGE = minimal_gauge()


class TestGenerateGaugeReportModuleFunction:
    """Tests for generate_gauge_report() defined in gauge_generator.py."""

    def test_basic_type_calls_generate_basic(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(GAUGE, output_dir=tmp_path,
                                  report_type="basic", auto_open=False)
        mock.generate_basic_report.assert_called_once()

    def test_monitoring_type_with_timeseries_calls_monitoring(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        ts = timeseries_data()
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(GAUGE, timeseries_data=ts,
                                  output_dir=tmp_path, report_type="monitoring",
                                  auto_open=False)
        mock.generate_monitoring_report.assert_called_once()

    def test_monitoring_without_timeseries_falls_back(self, tmp_path):
        """monitoring with no timeseries_data falls back to generate_report."""
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(GAUGE, timeseries_data=None,
                                  output_dir=tmp_path, report_type="monitoring",
                                  auto_open=False)
        mock.generate_report.assert_called_once()

    def test_analysis_type_calls_generate_analysis(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(GAUGE, output_dir=tmp_path,
                                  report_type="analysis", auto_open=False)
        mock.generate_analysis_report.assert_called_once()

    def test_unknown_type_calls_generate_report(self, tmp_path):
        mock, _ = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            generate_gauge_report(GAUGE, output_dir=tmp_path,
                                  report_type="unknown_type_xyz", auto_open=False)
        mock.generate_report.assert_called_once()

    def test_returns_path(self, tmp_path):
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=False)
        assert result == fake_pdf

    def test_auto_open_true_handles_exception(self, tmp_path):
        """auto_open=True with failing import → caught exception, still returns path."""
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=True)
        assert result is not None

    def test_auto_open_false_returns_path(self, tmp_path):
        mock, fake_pdf = _mock_gauge_generator(tmp_path)
        with patch("reports.gauge.gauge_generator.GaugeReportGenerator", return_value=mock):
            from reports.gauge.gauge_generator import generate_gauge_report
            result = generate_gauge_report(GAUGE, output_dir=tmp_path,
                                           report_type="basic", auto_open=False)
        assert result == fake_pdf
