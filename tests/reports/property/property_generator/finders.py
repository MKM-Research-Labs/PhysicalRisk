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

"""Tests for _find_property_by_id, _find_mortgage_by_property_id, open_pdf_file, and edge cases."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from .conftest import _minimal_property, _make_generator


class TestFindPropertyById:

    def test_properties_key_found(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"properties": [
            {"PropertyHeader": {"Header": {"PropertyID": "P-001"}}},
            {"PropertyHeader": {"Header": {"PropertyID": "P-002"}}},
        ]}
        result = _find_property_by_id(data, "P-002")
        assert result["PropertyHeader"]["Header"]["PropertyID"] == "P-002"

    def test_portfolio_key_found(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"portfolio": [{"PropertyHeader": {"Header": {"PropertyID": "PA"}}}]}
        result = _find_property_by_id(data, "PA")
        assert result["PropertyHeader"]["Header"]["PropertyID"] == "PA"

    def test_dict_without_list_key_wraps_itself(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"PropertyHeader": {"Header": {"PropertyID": "P-X"}}}
        result = _find_property_by_id(data, "P-X")
        assert result is data

    def test_list_input_found(self):
        from reports.property.property_generator import _find_property_by_id
        data = [{"PropertyHeader": {"Header": {"PropertyID": "P-L"}}}]
        result = _find_property_by_id(data, "P-L")
        assert result == data[0]

    def test_not_found_raises_value_error(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"properties": [{"PropertyHeader": {"Header": {"PropertyID": "P-001"}}}]}
        with pytest.raises(ValueError, match="P-999"):
            _find_property_by_id(data, "P-999")

    def test_invalid_type_raises_value_error(self):
        from reports.property.property_generator import _find_property_by_id
        with pytest.raises(ValueError):
            _find_property_by_id(42, "P-001")

    def test_none_raises_value_error(self):
        from reports.property.property_generator import _find_property_by_id
        with pytest.raises((ValueError, TypeError)):
            _find_property_by_id(None, "P-001")

    def test_empty_properties_list_raises(self):
        from reports.property.property_generator import _find_property_by_id
        with pytest.raises(ValueError):
            _find_property_by_id({"properties": []}, "P-001")

    def test_list_not_found_raises(self):
        from reports.property.property_generator import _find_property_by_id
        data = [{"PropertyHeader": {"Header": {"PropertyID": "P-001"}}}]
        with pytest.raises(ValueError):
            _find_property_by_id(data, "P-MISSING")


class TestFindMortgageByPropertyId:

    def test_dict_with_mortgages_found(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = {"mortgages": [{"PropertyID": "P-001", "amount": 100}]}
        result = _find_mortgage_by_property_id(data, "P-001")
        assert result["amount"] == 100

    def test_dict_with_mortgages_not_found_returns_none(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = {"mortgages": [{"PropertyID": "P-001"}]}
        result = _find_mortgage_by_property_id(data, "P-999")
        assert result is None

    def test_dict_without_mortgages_key_returns_data_itself(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = {"PropertyID": "P-001", "amount": 200}
        result = _find_mortgage_by_property_id(data, "P-001")
        assert result is not None

    def test_list_input_found(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = [{"PropertyID": "P-002", "amount": 200}]
        result = _find_mortgage_by_property_id(data, "P-002")
        assert result["amount"] == 200

    def test_list_input_not_found_returns_none(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = [{"PropertyID": "P-001"}]
        result = _find_mortgage_by_property_id(data, "P-MISSING")
        assert result is None

    def test_invalid_type_returns_data_as_is(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        result = _find_mortgage_by_property_id("some_string", "P-001")
        assert result == "some_string"

    def test_empty_mortgages_list_returns_none(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        result = _find_mortgage_by_property_id({"mortgages": []}, "P-001")
        assert result is None


class TestOpenPdfFile:

    def _fake_pdf(self, tmp_path: Path) -> Path:
        p = tmp_path / "report.pdf"
        p.write_bytes(b"%PDF-1.4")
        return p

    def test_darwin_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "open"

    def test_windows_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        mock_run.assert_called_once()

    def test_linux_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        args = mock_run.call_args[0][0]
        assert "xdg-open" in args

    def test_unknown_platform_uses_webbrowser(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", return_value="FreeBSD"):
            with patch("webbrowser.open") as mock_wb:
                result = open_pdf_file(fake)
        assert result is True
        mock_wb.assert_called_once()

    def test_subprocess_called_process_error_returns_false(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run",
                       side_effect=subprocess.CalledProcessError(1, "open")):
                result = open_pdf_file(fake)
        assert result is False

    def test_generic_exception_returns_false(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", side_effect=RuntimeError("no system")):
            result = open_pdf_file(fake)
        assert result is False

    def test_windows_case_insensitive(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = self._fake_pdf(tmp_path)
        with patch("platform.system", return_value="windows"):
            with patch("subprocess.run"):
                result = open_pdf_file(fake)
        assert isinstance(result, bool)


class TestEdgeCases:

    def test_completely_empty_property_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_property_only_report({})
        assert path.exists()

    def test_property_data_with_none_header(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_property_only_report({"PropertyHeader": None})
        assert path.exists()

    def test_zero_value_property(self, tmp_path):
        gen = _make_generator(tmp_path)
        data = _minimal_property()
        data["PropertyHeader"]["Valuation"]["PropertyValue"] = 0
        path = gen.generate_property_only_report(data)
        assert path.exists()

    def test_negative_value_property(self, tmp_path):
        gen = _make_generator(tmp_path)
        data = _minimal_property()
        data["PropertyHeader"]["Valuation"]["PropertyValue"] = -50_000
        path = gen.generate_property_only_report(data)
        assert path.exists()

    def test_report_with_all_pages(self, tmp_path, prop_data, mort_data):
        gen = _make_generator(tmp_path)
        all_pages = list(gen.property_pages.keys())
        path = gen.generate_report(prop_data, mortgage_data=mort_data,
                                   pages_to_include=all_pages)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_pdf_content_is_bytes(self, tmp_path, prop_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_property_only_report(prop_data)
        content = path.read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0
