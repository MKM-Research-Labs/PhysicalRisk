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

"""Tests for gauge PDF report generation."""

import pytest


class TestGaugePdfGeneration:
    """Test gauge PDF report generation end-to-end."""

    def test_basic_gauge_report_generates_pdf(self, tmp_path, sample_gauge_data):
        """Basic gauge report produces a valid PDF file."""
        from reports.gauge.gauge_generator import generate_gauge_report

        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            report_type='basic',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_full_gauge_report_generates_pdf(self, tmp_path, sample_gauge_data):
        """Full gauge report produces a valid PDF."""
        from reports.gauge.gauge_generator import generate_gauge_report

        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            report_type='full',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'

    def test_gauge_pdf_filename_contains_gauge_id(self, tmp_path, sample_gauge_data):
        """Generated filename includes the gauge ID."""
        from reports.gauge.gauge_generator import generate_gauge_report

        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            auto_open=False
        )

        assert 'GAUGE-test0001' in report_path.name

    def test_gauge_pdf_starts_with_pdf_header(self, tmp_path, sample_gauge_data):
        """Generated file is a valid PDF."""
        from reports.gauge.gauge_generator import generate_gauge_report

        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            auto_open=False
        )

        with open(report_path, 'rb') as f:
            header = f.read(5)
        assert header == b'%PDF-'

    def test_gauge_pdf_has_reasonable_size(self, tmp_path, sample_gauge_data):
        """Gauge report PDF should be non-trivial in size."""
        from reports.gauge.gauge_generator import generate_gauge_report

        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=tmp_path,
            auto_open=False
        )

        # Multi-page gauge report should be > 5KB
        assert report_path.stat().st_size > 5000

    def test_gauge_report_with_minimal_data(self, tmp_path):
        """Report handles minimal gauge data without crashing."""
        from reports.gauge.gauge_generator import generate_gauge_report

        minimal_data = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-minimal", "CatchmentID": "thames", "GaugeName": "Minimal Gauge"},
                "SensorStats": {},
                "SensorDetails": {"GaugeInformation": {}, "Measurements": {}},
                "FloodStage": {},
                "NRFAMetadata": {},
                "Location": {},
                "FloodStages": {}
            }
        }

        report_path = generate_gauge_report(
            gauge_data=minimal_data,
            output_dir=tmp_path,
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.stat().st_size > 0

    def test_gauge_output_dir_created_if_missing(self, tmp_path, sample_gauge_data):
        """Output directory is created automatically."""
        from reports.gauge.gauge_generator import generate_gauge_report

        new_dir = tmp_path / "nested" / "gauge_reports"
        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            output_dir=new_dir,
            auto_open=False
        )

        assert new_dir.exists()
        assert report_path.exists()


class TestGaugeReportGenerator:
    """Test GaugeReportGenerator class directly."""

    def test_generator_initialises(self, tmp_path):
        """Generator initialises with output directory."""
        from reports.gauge.gauge_generator import GaugeReportGenerator

        gen = GaugeReportGenerator(output_dir=tmp_path)
        assert gen.output_dir == tmp_path

    def test_list_available_pages(self, tmp_path):
        """Generator lists all registered gauge page modules."""
        from reports.gauge.gauge_generator import GaugeReportGenerator

        gen = GaugeReportGenerator(output_dir=tmp_path)
        pages = gen.list_available_pages()
        assert 'title_overview' in pages
        assert 'sensor_details' in pages
        assert 'data_summary' in pages
        assert 'flood_history' in pages
        assert 'hazard_curves' in pages
        assert 'prs_pricing' in pages
        assert 'current_risk' in pages
        assert 'trading' in pages
        assert len(pages) == 12

    def test_validate_pages(self, tmp_path):
        """Validates known gauge page names."""
        from reports.gauge.gauge_generator import GaugeReportGenerator

        gen = GaugeReportGenerator(output_dir=tmp_path)
        valid, invalid = gen.validate_pages(['title_overview', 'sensor_details', 'bogus'])
        assert 'title_overview' in valid
        assert 'bogus' in invalid
