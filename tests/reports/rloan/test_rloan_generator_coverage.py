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
Tests for missing coverage in reports.rloan.rloan_generator.

Covers:
- Lines 55-56: __init__ without output_dir (uses config default)
- Line 108: page_name not in self.pages (skip unknown page)
- Lines 116-118: exception in page.generate_elements (error handling)
- Lines 125-126: exception in _generate_filename (fallback to 'unknown')
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from tests.reports.pdf.conftest import sample_property_data, sample_mortgage_data


class TestMortgageGeneratorDefaultOutputDir:
    """Lines 55-56: __init__ with output_dir=None uses config."""

    def test_init_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        from config import config
        reports_dir = tmp_path / "property_reports"
        monkeypatch.setattr(config, "get_property_reports_dir", lambda: reports_dir)
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=None)
        assert gen.output_dir == reports_dir
        assert reports_dir.exists()


class TestMortgageGeneratorSkipUnknownPage:
    """Line 108: page_name not in self.pages -> continue."""

    def test_unknown_page_in_order_is_skipped(self, tmp_path, sample_property_data,
                                               sample_mortgage_data):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        # Insert a bogus page name that's not in self.pages
        gen.page_order = ['nonexistent_page'] + gen.page_order
        elements = gen._generate_elements(sample_property_data, sample_mortgage_data)
        # Should still produce elements from valid pages
        assert isinstance(elements, list)
        assert len(elements) > 0


class TestMortgageGeneratorPageException:
    """Lines 116-118: exception in page.generate_elements -> skip page."""

    def test_page_exception_is_caught(self, tmp_path, sample_property_data,
                                       sample_mortgage_data):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        # Replace one page with a mock that raises
        broken_page = MagicMock()
        broken_page.generate_elements.side_effect = RuntimeError("boom")
        gen.pages['title'] = broken_page
        elements = gen._generate_elements(sample_property_data, sample_mortgage_data)
        # Other pages should still contribute elements
        assert isinstance(elements, list)
        assert len(elements) > 0


class TestMortgageGeneratorFilenameFallback:
    """Lines 125-126: _generate_filename exception fallback to 'unknown'."""

    def test_generate_filename_none_mortgage_data(self, tmp_path):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        # Pass None which will cause AttributeError on .get()
        fname = gen._generate_filename(None)
        assert "unknown" in fname
        assert fname.endswith(".pdf")

    def test_generate_filename_non_dict_raises_attribute_error(self, tmp_path):
        from reports.rloan.rloan_generator import RLoanReportGenerator
        gen = RLoanReportGenerator(output_dir=tmp_path)
        # Pass an integer: .get() raises AttributeError -> caught -> 'unknown'
        fname = gen._generate_filename(42)
        assert "unknown" in fname
