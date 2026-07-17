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

"""Tests for DataLoader._load_with_validation."""

from unittest.mock import MagicMock

from .conftest import write_gauge


class TestLoadWithValidation:

    def test_successful_load_returns_data_dict(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = [{"id": "G1"}, {"id": "G2"}]
        result = dl._load_with_validation(mock_loader, "test_type")
        assert result is not None
        assert result["count"] == 2
        assert len(result["items"]) == 2

    def test_successful_load_records_valid_result(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = [{"id": "G1"}]
        dl._load_with_validation(mock_loader, "gauge_test")
        assert "gauge_test" in dl._validation_results
        assert dl._validation_results["gauge_test"].is_valid is True

    def test_empty_data_list_returns_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = []
        assert dl._load_with_validation(mock_loader, "empty_type") is None

    def test_empty_data_list_records_invalid_result(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = []
        dl._load_with_validation(mock_loader, "empty_type")
        assert dl._validation_results["empty_type"].is_valid is False
        assert "No data loaded" in dl._validation_results["empty_type"].errors

    def test_none_return_from_loader_returns_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = None
        assert dl._load_with_validation(mock_loader, "none_type") is None

    def test_exception_in_loader_returns_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.side_effect = RuntimeError("disk error")
        assert dl._load_with_validation(mock_loader, "error_type") is None

    def test_exception_records_error_in_validation(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.side_effect = RuntimeError("disk error")
        dl._load_with_validation(mock_loader, "error_type")
        assert dl._validation_results["error_type"].is_valid is False
        assert "disk error" in dl._validation_results["error_type"].errors[0]

    def test_validation_summary_has_type_field(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = [{"id": "X"}]
        dl._load_with_validation(mock_loader, "xtype")
        assert dl._validation_results["xtype"].summary["type"] == "xtype"

    def test_validation_summary_count_matches_items(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
        dl._load_with_validation(mock_loader, "three_items")
        assert dl._validation_results["three_items"].summary["count"] == 3
