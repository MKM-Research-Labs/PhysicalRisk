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
Tests for reports.rloan — RLoanTitlePage and RLoanReportGenerator.

Covers: generate_elements (full data, empty data, no mortgage_data),
RLoanReportGenerator.__init__, _generate_filename, _generate_elements,
and generate_rloan_report convenience function.
"""

import pytest


# ===========================================================================
# RLoanTitlePage
# ===========================================================================

class TestRLoanTitlePage:

    def test_returns_list(self, sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_page_01_title import RLoanTitlePage
        page = RLoanTitlePage()
        elements = page.generate_elements(sample_property_data, sample_mortgage_data)
        assert isinstance(elements, list)

    def test_elements_non_empty(self, sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_page_01_title import RLoanTitlePage
        page = RLoanTitlePage()
        elements = page.generate_elements(sample_property_data, sample_mortgage_data)
        assert len(elements) > 0

    def test_no_mortgage_data_returns_elements(self, sample_property_data):
        from reports.rloan.rloan_page_01_title import RLoanTitlePage
        page = RLoanTitlePage()
        elements = page.generate_elements(sample_property_data, None)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_empty_property_data_does_not_crash(self, sample_mortgage_data):
        from reports.rloan.rloan_page_01_title import RLoanTitlePage
        page = RLoanTitlePage()
        elements = page.generate_elements({}, sample_mortgage_data)
        assert isinstance(elements, list)

    def test_extracts_mortgage_id(self, sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_page_01_title import RLoanTitlePage
        from reportlab.platypus import Paragraph
        page = RLoanTitlePage()
        elements = page.generate_elements(sample_property_data, sample_mortgage_data)
        # Find paragraph elements and check for mortgage ID text
        para_texts = [
            e.text for e in elements
            if hasattr(e, 'text') and e.text
        ]
        full_text = " ".join(para_texts)
        assert "MORT-test0001" in full_text

    def test_table_elements_included(self, sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_page_01_title import RLoanTitlePage
        from reportlab.platypus import Table
        page = RLoanTitlePage()
        elements = page.generate_elements(sample_property_data, sample_mortgage_data)
        tables = [e for e in elements if isinstance(e, Table)]
        assert len(tables) >= 1


# ===========================================================================
# RLoanReportGenerator
# ===========================================================================

class TestRLoanReportGenerator:

    def test_init_creates_output_dir(self, tmp_path):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        output_dir = tmp_path / "reports"
        gen = RLoanReportGenerator(output_dir=output_dir)
        assert output_dir.exists()

    def test_pages_initialised(self, tmp_path):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        assert "title" in gen.pages
        assert "mortgage_overview" in gen.pages

    def test_page_order_set(self, tmp_path):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        assert "title" in gen.page_order
        assert gen.page_order[0] == "title"

    def test_generate_filename_with_id(self, tmp_path, sample_mortgage_data):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        fname = gen._generate_filename(sample_mortgage_data)
        assert "MORT-test0001" in fname
        assert fname.endswith(".pdf")

    def test_generate_filename_fallback(self, tmp_path):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        fname = gen._generate_filename({})
        assert fname.endswith(".pdf")
        assert "unknown" in fname

    def test_generate_elements_returns_list(self, tmp_path,
                                            sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        elements = gen._generate_elements(sample_property_data, sample_mortgage_data)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_generate_report_creates_pdf(self, tmp_path,
                                         sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        output = gen.generate_report(
            sample_property_data, sample_mortgage_data,
            output_filename="test_mortgage.pdf"
        )
        assert output.exists()
        assert output.suffix == ".pdf"

    def test_generate_report_returns_path(self, tmp_path,
                                          sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        from pathlib import Path
        gen = RLoanReportGenerator(output_dir=tmp_path)
        result = gen.generate_report(
            sample_property_data, sample_mortgage_data,
            output_filename="test2.pdf"
        )
        assert isinstance(result, Path)


# ===========================================================================
# generate_rloan_report convenience function
# ===========================================================================

class TestGenerateMortgageReport:

    def test_convenience_function_creates_pdf(self, tmp_path,
                                               sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_generator import generate_rloan_report
        output = generate_rloan_report(
            sample_property_data, sample_mortgage_data,
            output_dir=tmp_path
        )
        assert output.exists()

    def test_convenience_function_returns_path(self, tmp_path,
                                                sample_property_data, sample_mortgage_data):
        from reports.rloan.rloan_generator import generate_rloan_report
        from pathlib import Path
        result = generate_rloan_report(
            sample_property_data, sample_mortgage_data,
            output_dir=tmp_path
        )
        assert isinstance(result, Path)
