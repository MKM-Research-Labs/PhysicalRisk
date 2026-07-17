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

"""Tests for property PDF report generation."""

import pytest


class TestPropertyPdfGeneration:
    """Test property PDF report generation end-to-end."""

    def test_full_property_report_generates_pdf(self, tmp_path, sample_property_data, sample_mortgage_data):
        """Full property+mortgage report produces a valid PDF file."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            rloan_data=sample_mortgage_data,
            output_dir=tmp_path,
            report_type='full',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_property_only_report_generates_pdf(self, tmp_path, sample_property_data):
        """Property-only report (no mortgage) produces a valid PDF."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            rloan_data=None,
            output_dir=tmp_path,
            report_type='property-only',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_risk_focused_report_generates_pdf(self, tmp_path, sample_property_data, sample_mortgage_data):
        """Risk-focused report produces a valid PDF."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            rloan_data=sample_mortgage_data,
            output_dir=tmp_path,
            report_type='risk-focused',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_mortgage_focused_report_generates_pdf(self, tmp_path, sample_property_data, sample_mortgage_data):
        """Mortgage-focused report produces a valid PDF."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            rloan_data=sample_mortgage_data,
            output_dir=tmp_path,
            report_type='mortgage-focused',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_pdf_filename_contains_property_id(self, tmp_path, sample_property_data):
        """Generated filename includes the property ID."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            output_dir=tmp_path,
            auto_open=False
        )

        assert 'PROP-test0001' in report_path.name

    def test_pdf_has_reasonable_size(self, tmp_path, sample_property_data, sample_mortgage_data):
        """Full report PDF should be non-trivial in size (multi-page)."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            rloan_data=sample_mortgage_data,
            output_dir=tmp_path,
            auto_open=False
        )

        # A multi-page PDF with 18 pages should be > 10KB
        assert report_path.stat().st_size > 10000

    def test_pdf_starts_with_pdf_header(self, tmp_path, sample_property_data):
        """Generated file is a valid PDF (starts with %PDF)."""
        from reports.property.property_generator import generate_property_report

        report_path = generate_property_report(
            property_data=sample_property_data,
            output_dir=tmp_path,
            auto_open=False
        )

        with open(report_path, 'rb') as f:
            header = f.read(5)
        assert header == b'%PDF-'

    def test_output_dir_created_if_missing(self, tmp_path, sample_property_data):
        """Output directory is created automatically if it doesn't exist."""
        from reports.property.property_generator import generate_property_report

        new_dir = tmp_path / "nested" / "reports"
        report_path = generate_property_report(
            property_data=sample_property_data,
            output_dir=new_dir,
            auto_open=False
        )

        assert new_dir.exists()
        assert report_path.exists()

    def test_report_with_minimal_property_data(self, tmp_path):
        """Report handles minimal/sparse property data without crashing."""
        from reports.property.property_generator import generate_property_report

        minimal_data = {
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-minimal"},
                "Valuation": {},
                "PropertyAttributes": {},
                "Construction": {},
                "Location": {},
                "RiskAssessment": {}
            },
            "ProtectionMeasures": {},
            "TransactionHistory": {}
        }

        report_path = generate_property_report(
            property_data=minimal_data,
            output_dir=tmp_path,
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.stat().st_size > 0


class TestPropertyReportGenerator:
    """Test PropertyReportGenerator class directly."""

    def test_generator_initialises(self, tmp_path):
        """Generator initialises with output directory."""
        from reports.property.property_generator import PropertyReportGenerator

        gen = PropertyReportGenerator(output_dir=tmp_path)
        assert gen.output_dir == tmp_path

    def test_list_available_pages(self, tmp_path):
        """Generator lists all registered page modules."""
        from reports.property.property_generator import PropertyReportGenerator

        gen = PropertyReportGenerator(output_dir=tmp_path)
        pages = gen.list_available_pages()
        assert 'title_overview' in pages
        assert 'location' in pages
        assert 'data_summary' in pages
        assert len(pages) == 17

    def test_validate_pages_valid(self, tmp_path):
        """Validates known page names."""
        from reports.property.property_generator import PropertyReportGenerator

        gen = PropertyReportGenerator(output_dir=tmp_path)
        valid, invalid = gen.validate_pages(['title_overview', 'location', 'bogus_page'])
        assert 'title_overview' in valid
        assert 'location' in valid
        assert 'bogus_page' in invalid

    def test_auto_select_pages_without_mortgage(self, tmp_path, sample_property_data):
        """Auto-select excludes mortgage pages when no mortgage data."""
        from reports.property.property_generator import PropertyReportGenerator

        gen = PropertyReportGenerator(output_dir=tmp_path)
        pages = gen._auto_select_pages(sample_property_data, None)
        assert 'title_overview' in pages
        assert 'mortgage_overview' not in pages
        assert 'data_summary' in pages

    def test_auto_select_pages_with_mortgage(self, tmp_path, sample_property_data, sample_mortgage_data):
        """Auto-select includes mortgage pages when mortgage data present."""
        from reports.property.property_generator import PropertyReportGenerator

        gen = PropertyReportGenerator(output_dir=tmp_path)
        pages = gen._auto_select_pages(sample_property_data, sample_mortgage_data)
        assert 'mortgage_overview' in pages
        assert 'mortgage_details' in pages
