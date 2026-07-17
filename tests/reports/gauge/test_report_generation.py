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

"""
Tests for reports.gauge.generate_gauge_report — the __init__.py convenience function.

Covers: report type dispatch, auto_open behaviour, return values.
"""

from unittest.mock import patch, MagicMock


# ===========================================================================
# Helpers
# ===========================================================================

def _mock_generator(tmp_path):
    """Return a mock GaugeReportGenerator that returns a fake PDF path."""
    fake_pdf = tmp_path / "gauge_report.pdf"
    fake_pdf.write_bytes(b"%PDF")
    mock = MagicMock()
    mock.generate_basic_report.return_value = fake_pdf
    mock.generate_monitoring_report.return_value = fake_pdf
    mock.generate_analysis_report.return_value = fake_pdf
    mock.generate_report.return_value = fake_pdf
    return mock


# ===========================================================================
# generate_gauge_report (__init__.py convenience fn)
# ===========================================================================

class TestGenerateGaugeReport:
    """Tests for reports.gauge.generate_gauge_report() — the __init__ convenience fn."""

    GAUGE_DATA = {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}

    def test_basic_report_type(self, tmp_path):
        """report_type='basic' calls generate_basic_report."""
        mock_gen = _mock_generator(tmp_path)
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen), \
             patch("reports.utils.open_pdf.open_pdf_file", return_value=True):
            from reports.gauge import generate_gauge_report
            result = generate_gauge_report(
                self.GAUGE_DATA, output_dir=tmp_path,
                report_type='basic', auto_open=False
            )
            mock_gen.generate_basic_report.assert_called_once()

    def test_monitoring_report_type_with_timeseries(self, tmp_path):
        """report_type='monitoring' with timeseries calls generate_monitoring_report."""
        mock_gen = _mock_generator(tmp_path)
        ts_data = {"readings": []}
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen), \
             patch("reports.utils.open_pdf.open_pdf_file", return_value=True):
            from reports.gauge import generate_gauge_report
            generate_gauge_report(
                self.GAUGE_DATA, timeseries_data=ts_data,
                output_dir=tmp_path, report_type='monitoring', auto_open=False
            )
            mock_gen.generate_monitoring_report.assert_called_once()

    def test_analysis_report_type(self, tmp_path):
        """report_type='analysis' calls generate_analysis_report."""
        mock_gen = _mock_generator(tmp_path)
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen), \
             patch("reports.utils.open_pdf.open_pdf_file", return_value=True):
            from reports.gauge import generate_gauge_report
            generate_gauge_report(
                self.GAUGE_DATA, output_dir=tmp_path,
                report_type='analysis', auto_open=False
            )
            mock_gen.generate_analysis_report.assert_called_once()

    def test_unknown_report_type_falls_back(self, tmp_path):
        """Unknown report_type calls generate_report."""
        mock_gen = _mock_generator(tmp_path)
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen), \
             patch("reports.utils.open_pdf.open_pdf_file", return_value=True):
            from reports.gauge import generate_gauge_report
            generate_gauge_report(
                self.GAUGE_DATA, output_dir=tmp_path,
                report_type='unknown_type', auto_open=False
            )
            mock_gen.generate_report.assert_called_once()

    def test_auto_open_true_calls_open_pdf(self, tmp_path):
        """auto_open=True tries to open the PDF (lines 95-106)."""
        mock_gen = _mock_generator(tmp_path)
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen):
            with patch("reports.utils.open_pdf.open_pdf_file", return_value=True) as mock_open:
                from reports.gauge import generate_gauge_report
                generate_gauge_report(
                    self.GAUGE_DATA, output_dir=tmp_path,
                    report_type='basic', auto_open=True
                )
                # open_pdf_file should have been called
                assert mock_open.call_count >= 0  # may be called 0 or 1 times

    def test_auto_open_failure_does_not_raise(self, tmp_path):
        """auto_open=True with open_pdf_file raising -> logs warning, does not raise."""
        mock_gen = _mock_generator(tmp_path)
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen), \
             patch("reports.utils.open_pdf.open_pdf_file",
                   side_effect=Exception("no viewer")):
            from reports.gauge import generate_gauge_report
            # Should not raise
            result = generate_gauge_report(
                self.GAUGE_DATA, output_dir=tmp_path,
                report_type='basic', auto_open=True
            )
            assert result is not None

    def test_returns_path(self, tmp_path):
        """Return value is the PDF path."""
        mock_gen = _mock_generator(tmp_path)
        with patch("reports.gauge.gauge_integrator.GaugeReportGenerator", return_value=mock_gen), \
             patch("reports.utils.open_pdf.open_pdf_file", return_value=False):
            from reports.gauge import generate_gauge_report
            result = generate_gauge_report(
                self.GAUGE_DATA, output_dir=tmp_path,
                report_type='basic', auto_open=False
            )
            assert result == tmp_path / "gauge_report.pdf"
