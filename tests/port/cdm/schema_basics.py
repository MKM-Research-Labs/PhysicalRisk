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

"""Parametrized tests for all CDM schema basics."""

import pytest


ALL_CDM_FIXTURES = [
    "gauge_cdm", "property_cdm", "mortgage_cdm",
    "storm_cdm", "stormts_cdm", "prs_cdm",
]


class TestCDMSchemaBasics:
    """Test that each CDM provides a valid schema structure."""

    @pytest.mark.parametrize("cdm_name", ALL_CDM_FIXTURES)
    def test_schema_returns_non_empty_dict(self, cdm_name, request):
        cdm = request.getfixturevalue(cdm_name)
        schema = cdm.schema
        assert isinstance(schema, dict)
        assert len(schema) > 0

    @pytest.mark.parametrize("cdm_name", ALL_CDM_FIXTURES)
    def test_list_all_fields_returns_paths(self, cdm_name, request):
        cdm = request.getfixturevalue(cdm_name)
        fields = cdm.list_all_fields()
        assert isinstance(fields, list)
        assert len(fields) > 0
        for field in fields:
            assert isinstance(field, str)
            assert "." in field

    @pytest.mark.parametrize("cdm_name", ALL_CDM_FIXTURES)
    def test_get_required_fields_returns_list(self, cdm_name, request):
        cdm = request.getfixturevalue(cdm_name)
        assert isinstance(cdm.get_required_fields(), list)

    @pytest.mark.parametrize("cdm_name", ALL_CDM_FIXTURES)
    def test_repr_returns_string(self, cdm_name, request):
        cdm = request.getfixturevalue(cdm_name)
        assert isinstance(repr(cdm), str)
