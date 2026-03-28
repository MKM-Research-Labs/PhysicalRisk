# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for PropertyReportGenerator.__init__, _auto_select_pages, _generate_filename."""

from pathlib import Path
from unittest.mock import patch

from .conftest import _make_generator


class TestPropertyReportGeneratorInit:

    def test_explicit_output_dir_string(self, tmp_path):
        from reports.property.property_generator import PropertyReportGenerator
        gen = PropertyReportGenerator(output_dir=str(tmp_path))
        assert gen.output_dir == tmp_path

    def test_explicit_output_dir_path(self, tmp_path):
        from reports.property.property_generator import PropertyReportGenerator
        gen = PropertyReportGenerator(output_dir=tmp_path)
        assert isinstance(gen.output_dir, Path)

    def test_output_dir_created(self, tmp_path):
        from reports.property.property_generator import PropertyReportGenerator
        new_dir = tmp_path / "brand_new_dir"
        PropertyReportGenerator(output_dir=new_dir)
        assert new_dir.exists()

    def test_no_output_dir_uses_config(self, tmp_path, monkeypatch):
        from config import config
        prop_dir = tmp_path / "prop_reports"
        monkeypatch.setattr(config, "get_property_reports_dir", lambda: prop_dir)
        from reports.property.property_generator import PropertyReportGenerator
        gen = PropertyReportGenerator()
        assert gen.output_dir == prop_dir

    def test_property_pages_dict_initialized(self, tmp_path):
        gen = _make_generator(tmp_path)
        expected = {
            "title_overview", "location", "attributes", "construction",
            "risk_assessment", "financial", "protection", "history", "transactions",
            "mortgage_overview", "mortgage_details", "mortgage_costs",
            "regulatory", "current_status", "borrower_profile",
            "risk_analysis", "data_summary",
        }
        assert expected <= set(gen.pages.keys())

    def test_categories_dict_initialized(self, tmp_path):
        gen = _make_generator(tmp_path)
        assert "property" in gen.categories
        assert "mortgage" in gen.categories
        assert "analysis" in gen.categories


class TestAutoSelectPages:

    def test_without_mortgage_excludes_mortgage_pages(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, None)
        for mp in gen.categories["mortgage"]:
            assert mp not in pages

    def test_with_mortgage_includes_mortgage_pages(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, mort_data)
        for mp in gen.categories["mortgage"]:
            assert mp in pages

    def test_always_includes_analysis_pages(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, None)
        for ap in gen.categories["analysis"]:
            assert ap in pages

    def test_always_includes_property_pages(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, None)
        for pp in gen.categories["property"]:
            assert pp in pages

    def test_empty_property_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        pages = gen._auto_select_pages({}, None)
        assert isinstance(pages, list)


class TestGenerateFilename:

    def test_returns_string(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename(prop_data)
        assert isinstance(name, str)

    def test_ends_with_pdf(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        assert gen._generate_filename(prop_data).endswith(".pdf")

    def test_contains_property_id(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename(prop_data)
        assert "PROP-001" in name

    def test_missing_property_id_uses_unknown(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename({})
        assert "unknown" in name
        assert name.endswith(".pdf")

    def test_partial_path_missing_header(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename({"PropertyHeader": {}})
        assert "unknown" in name

    def test_partial_path_missing_property_id(self, tmp_path):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename({"PropertyHeader": {"Header": {}}})
        assert "unknown" in name

    def test_timestamp_in_filename(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        name = gen._generate_filename(prop_data)
        digits = sum(c.isdigit() for c in name)
        assert digits >= 8
