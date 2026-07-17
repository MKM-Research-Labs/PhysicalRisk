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

"""Tests for LoadedData and DataValidationResult data structures."""

import dataclasses


class TestLoadedData:

    def test_defaults_are_none(self):
        from visual.core.data_loader import LoadedData
        d = LoadedData()
        for field in ("gauge_data", "property_data", "rloan_data",
                      "hazard_data", "property_hazard_data",
                      "storm_data", "counterparty_data"):
            assert getattr(d, field) is None

    def test_lookup_defaults_are_none(self):
        from visual.core.data_loader import LoadedData
        d = LoadedData()
        for field in ("rloan_lookup", "gauge_flood_info",
                      "property_flood_info"):
            assert getattr(d, field) is None

    def test_counts_default_to_zero(self):
        from visual.core.data_loader import LoadedData
        d = LoadedData()
        assert d.gaugets_count == 0
        assert d.gaugehd_count == 0
        assert d.propertyts_count == 0

    def test_can_set_gauge_data(self):
        from visual.core.data_loader import LoadedData
        d = LoadedData(gauge_data={"items": []})
        assert d.gauge_data is not None

    def test_can_set_multiple_fields(self):
        from visual.core.data_loader import LoadedData
        d = LoadedData(gauge_data={}, property_data={},
                       gaugets_count=3, gaugehd_count=5)
        assert d.gaugets_count == 3
        assert d.gaugehd_count == 5

    def test_is_dataclass(self):
        from visual.core.data_loader import LoadedData
        assert dataclasses.is_dataclass(LoadedData)


class TestDataValidationResult:

    def test_is_named_tuple(self):
        from visual.core.data_loader import DataValidationResult
        result = DataValidationResult(True, [], [], {"type": "gauge"})
        assert isinstance(result, tuple)

    def test_valid_result_fields(self):
        from visual.core.data_loader import DataValidationResult
        result = DataValidationResult(True, ["minor issue"], [], {"count": 5})
        assert result.is_valid is True
        assert result.warnings == ["minor issue"]
        assert result.errors == []
        assert result.summary["count"] == 5

    def test_invalid_result_fields(self):
        from visual.core.data_loader import DataValidationResult
        result = DataValidationResult(False, [], ["file not found"], {"loaded": False})
        assert result.is_valid is False
        assert "file not found" in result.errors

    def test_tuple_unpacking(self):
        from visual.core.data_loader import DataValidationResult
        is_valid, warnings, errors, summary = DataValidationResult(True, [], [], {})
        assert is_valid is True
