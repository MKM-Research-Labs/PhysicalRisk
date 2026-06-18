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

"""Tests for _auto_select_pages, _generate_filename, and utility methods."""

from .conftest import make_generator, minimal_property, minimal_mortgage


# ===========================================================================
# TestAutoSelectPages
# ===========================================================================

class TestAutoSelectPages:

    def test_without_mortgage_excludes_mortgage_pages(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, None)
        for mp in gen.categories["mortgage"]:
            assert mp not in pages

    def test_with_mortgage_includes_mortgage_pages(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, mort_data)
        for mp in gen.categories["mortgage"]:
            assert mp in pages

    def test_always_includes_analysis_pages(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, None)
        for ap in gen.categories["analysis"]:
            assert ap in pages

    def test_always_includes_property_pages(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages(prop_data, None)
        for pp in gen.categories["property"]:
            assert pp in pages

    def test_empty_property_data(self, tmp_path):
        gen = make_generator(tmp_path)
        pages = gen._auto_select_pages({}, None)
        assert isinstance(pages, list)


# ===========================================================================
# TestGenerateFilename
# ===========================================================================

class TestGenerateFilename:

    def test_returns_string(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert isinstance(gen._generate_filename(prop_data), str)

    def test_ends_with_pdf(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen._generate_filename(prop_data).endswith(".pdf")

    def test_contains_property_id(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert "PROP-001" in gen._generate_filename(prop_data)

    def test_missing_property_id_uses_unknown(self, tmp_path):
        gen = make_generator(tmp_path)
        name = gen._generate_filename({})
        assert "unknown" in name
        assert name.endswith(".pdf")

    def test_partial_path_missing_header(self, tmp_path):
        gen = make_generator(tmp_path)
        assert "unknown" in gen._generate_filename({"PropertyHeader": {}})

    def test_partial_path_missing_property_id(self, tmp_path):
        gen = make_generator(tmp_path)
        assert "unknown" in gen._generate_filename({"PropertyHeader": {"Header": {}}})

    def test_timestamp_in_filename(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        name = gen._generate_filename(prop_data)
        assert sum(c.isdigit() for c in name) >= 8


# ===========================================================================
# TestUtilityMethods
# ===========================================================================

class TestUtilityMethods:

    def test_list_available_pages_returns_list(self, tmp_path):
        gen = make_generator(tmp_path)
        assert isinstance(gen.list_available_pages(), list)

    def test_list_available_pages_contains_all_expected(self, tmp_path):
        gen = make_generator(tmp_path)
        expected = {
            "title_overview", "location", "attributes", "construction",
            "risk_assessment", "financial", "protection", "history", "transactions",
            "mortgage_overview", "mortgage_details", "mortgage_costs",
            "regulatory", "current_status", "borrower_profile",
            "risk_analysis", "data_summary",
        }
        assert expected <= set(gen.list_available_pages())

    def test_get_page_categories_returns_dict(self, tmp_path):
        gen = make_generator(tmp_path)
        assert isinstance(gen.get_page_categories(), dict)

    def test_get_page_categories_returns_copy(self, tmp_path):
        gen = make_generator(tmp_path)
        cats = gen.get_page_categories()
        cats["__new_key__"] = []
        assert "__new_key__" not in gen.categories

    def test_validate_pages_all_valid(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "data_summary"])
        assert "title_overview" in valid
        assert "data_summary" in valid
        assert invalid == []

    def test_validate_pages_all_invalid(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["no_such_page", "another_bogus"])
        assert valid == []
        assert "no_such_page" in invalid
        assert "another_bogus" in invalid

    def test_validate_pages_mixed(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages(["title_overview", "nonexistent_page"])
        assert "title_overview" in valid
        assert "nonexistent_page" in invalid

    def test_validate_pages_empty_list(self, tmp_path):
        gen = make_generator(tmp_path)
        valid, invalid = gen.validate_pages([])
        assert valid == []
        assert invalid == []
