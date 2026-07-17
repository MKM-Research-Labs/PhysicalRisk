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
Tests for helper functions in reports.property.property_generator.

Covers: _find_property_by_id, open_pdf_file, _find_mortgage_by_property_id.
"""

import subprocess
from unittest.mock import patch

import pytest


# ===========================================================================
# _find_property_by_id
# ===========================================================================

class TestFindPropertyById:
    """Tests for _find_property_by_id (lines 378-397)."""

    def test_properties_key(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"properties": [{"PropertyHeader": {"Header": {"PropertyID": "PROP-001"}}}]}
        result = _find_property_by_id(data, "PROP-001")
        assert result == data["properties"][0]

    def test_portfolio_key(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"portfolio": [{"PropertyHeader": {"Header": {"PropertyID": "PROP-A"}}}]}
        result = _find_property_by_id(data, "PROP-A")
        assert result == data["portfolio"][0]

    def test_dict_without_properties_wraps_in_list(self):
        from reports.property.property_generator import _find_property_by_id
        # Dict without 'properties' or 'portfolio' key -> wraps as single item
        # But then searching for PropertyID inside the wrapper won't match
        # (it's actually searching data itself as a property)
        data = {"PropertyHeader": {"Header": {"PropertyID": "PROP-X"}}}
        result = _find_property_by_id(data, "PROP-X")
        assert result == data

    def test_list_input(self):
        from reports.property.property_generator import _find_property_by_id
        data = [{"PropertyHeader": {"Header": {"PropertyID": "PROP-LIST"}}}]
        result = _find_property_by_id(data, "PROP-LIST")
        assert result == data[0]

    def test_not_found_raises(self):
        from reports.property.property_generator import _find_property_by_id
        data = {"properties": [{"PropertyHeader": {"Header": {"PropertyID": "PROP-001"}}}]}
        with pytest.raises(ValueError, match="PROP-999"):
            _find_property_by_id(data, "PROP-999")

    def test_invalid_type_raises(self):
        from reports.property.property_generator import _find_property_by_id
        with pytest.raises(ValueError):
            _find_property_by_id(42, "PROP-001")


# ===========================================================================
# open_pdf_file
# ===========================================================================

class TestOpenPdfFile:
    """Tests for open_pdf_file (lines 353-374)."""

    def test_darwin_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = tmp_path / "report.pdf"
        fake.write_bytes(b"%PDF")
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        mock_run.assert_called_once()

    def test_windows_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = tmp_path / "report.pdf"
        fake.write_bytes(b"%PDF")
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True

    def test_linux_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = tmp_path / "report.pdf"
        fake.write_bytes(b"%PDF")
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True

    def test_unknown_platform_uses_webbrowser(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = tmp_path / "report.pdf"
        fake.write_bytes(b"%PDF")
        with patch("platform.system", return_value="FreeBSD"):
            with patch("webbrowser.open") as mock_wb:
                result = open_pdf_file(fake)
        assert result is True
        mock_wb.assert_called_once()

    def test_subprocess_failure_returns_false(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = tmp_path / "report.pdf"
        fake.write_bytes(b"%PDF")
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "open")):
                result = open_pdf_file(fake)
        assert result is False

    def test_generic_exception_returns_false(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = tmp_path / "report.pdf"
        fake.write_bytes(b"%PDF")
        with patch("platform.system", side_effect=RuntimeError("boom")):
            result = open_pdf_file(fake)
        assert result is False


# ===========================================================================
# _find_mortgage_by_property_id
# ===========================================================================

class TestFindMortgageByPropertyId:
    """Tests for _find_mortgage_by_property_id (lines 400-413)."""

    def test_dict_with_mortgages_found(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = {"loans": [{"PropertyID": "PROP-001", "amount": 100}]}
        result = _find_mortgage_by_property_id(data, "PROP-001")
        assert result["amount"] == 100

    def test_dict_with_mortgages_not_found_returns_none(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = {"loans": [{"PropertyID": "PROP-001"}]}
        result = _find_mortgage_by_property_id(data, "PROP-999")
        assert result is None

    def test_list_input_found(self):
        from reports.property.property_generator import _find_mortgage_by_property_id
        data = [{"PropertyID": "PROP-002", "amount": 200}]
        result = _find_mortgage_by_property_id(data, "PROP-002")
        assert result["amount"] == 200

    def test_invalid_type_returns_data(self):
        """Lines 406-407: non-dict, non-list -> return data as-is."""
        from reports.property.property_generator import _find_mortgage_by_property_id
        result = _find_mortgage_by_property_id("some_string", "PROP-001")
        assert result == "some_string"
