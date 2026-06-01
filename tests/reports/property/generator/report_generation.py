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

"""Tests for generate_report, specialised report methods, and edge cases."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from .conftest import make_generator, minimal_property


# ===========================================================================
# TestGenerateReport
# ===========================================================================

class TestGenerateReport:

    def test_returns_path(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert isinstance(gen.generate_report(prop_data), Path)

    def test_pdf_exists(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(prop_data).exists()

    def test_pdf_non_empty(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(prop_data).stat().st_size > 0

    def test_pdf_suffix(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(prop_data).suffix == ".pdf"

    def test_custom_output_filename(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(prop_data, output_filename="my_prop.pdf")
        assert path.name == "my_prop.pdf"
        assert path.exists()

    def test_custom_pages_to_include(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(prop_data, pages_to_include=["title_overview", "data_summary"])
        assert path.exists()

    def test_with_mortgage_data(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(prop_data, rloan_data=mort_data).exists()

    def test_auto_select_called_when_pages_none(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(prop_data, pages_to_include=None)
        spy.assert_called_once()

    def test_auto_select_not_called_when_pages_provided(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        with patch.object(gen, "_auto_select_pages", wraps=gen._auto_select_pages) as spy:
            gen.generate_report(prop_data, pages_to_include=["title_overview"])
        spy.assert_not_called()

    def test_empty_property_data(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen.generate_report({}).exists()

    def test_full_data_report(self, tmp_path, full_prop_data, mort_data):
        gen = make_generator(tmp_path)
        path = gen.generate_report(full_prop_data, rloan_data=mort_data)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_all_unknown_pages_still_creates_pdf(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen.generate_report(prop_data, pages_to_include=["xxx", "yyy"]).exists()


# ===========================================================================
# TestSpecialisedReportMethods
# ===========================================================================

class TestSpecialisedReportMethods:

    def test_generate_property_only_report_exists(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen.generate_property_only_report(prop_data).exists()

    def test_generate_property_only_report_custom_filename(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        path = gen.generate_property_only_report(prop_data, output_filename="prop_only.pdf")
        assert path.name == "prop_only.pdf"

    def test_generate_mortgage_focused_report_exists(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        assert gen.generate_mortgage_focused_report(prop_data, mort_data).exists()

    def test_generate_mortgage_focused_report_custom_filename(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        path = gen.generate_mortgage_focused_report(
            prop_data, mort_data, output_filename="mort_focused.pdf"
        )
        assert path.name == "mort_focused.pdf"

    def test_generate_risk_focused_report_with_mortgage(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        assert gen.generate_risk_focused_report(prop_data, mort_data).exists()

    def test_generate_risk_focused_report_without_mortgage(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        assert gen.generate_risk_focused_report(prop_data).exists()

    def test_generate_risk_focused_report_custom_filename(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        path = gen.generate_risk_focused_report(prop_data, output_filename="risk_only.pdf")
        assert path.name == "risk_only.pdf"

    def test_mortgage_focused_includes_mortgage_overview(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["mortgage_overview"])
        gen.pages["mortgage_overview"] = spy
        gen.generate_mortgage_focused_report(prop_data, mort_data)
        spy.generate_elements.assert_called_once()

    def test_risk_focused_with_mortgage_includes_current_status(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["current_status"])
        gen.pages["current_status"] = spy
        gen.generate_risk_focused_report(prop_data, mort_data)
        spy.generate_elements.assert_called_once()

    def test_risk_focused_without_mortgage_excludes_current_status(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        spy = MagicMock(wraps=gen.pages["current_status"])
        gen.pages["current_status"] = spy
        gen.generate_risk_focused_report(prop_data)
        spy.generate_elements.assert_not_called()


# ===========================================================================
# TestEdgeCases
# ===========================================================================

class TestEdgeCases:

    def test_completely_empty_property_data(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen.generate_property_only_report({}).exists()

    def test_property_data_with_none_header(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen.generate_property_only_report({"PropertyHeader": None}).exists()

    def test_zero_value_property(self, tmp_path):
        gen = make_generator(tmp_path)
        data = minimal_property()
        data["PropertyHeader"]["Valuation"]["PropertyValue"] = 0
        assert gen.generate_property_only_report(data).exists()

    def test_negative_value_property(self, tmp_path):
        gen = make_generator(tmp_path)
        data = minimal_property()
        data["PropertyHeader"]["Valuation"]["PropertyValue"] = -50_000
        assert gen.generate_property_only_report(data).exists()

    def test_report_with_all_pages(self, tmp_path, prop_data, mort_data):
        gen = make_generator(tmp_path)
        all_pages = list(gen.pages.keys())
        path = gen.generate_report(prop_data, rloan_data=mort_data, pages_to_include=all_pages)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_pdf_content_is_bytes(self, tmp_path, prop_data):
        gen = make_generator(tmp_path)
        content = gen.generate_property_only_report(prop_data).read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0
