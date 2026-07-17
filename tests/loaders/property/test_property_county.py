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

"""Tests for PropertyLoader.find_by_county() — missing lines 164-175."""

import json
from pathlib import Path

import pytest

from tests.loaders.conftest import write_json


def _property_json_with_counties():
    """Properties with County field populated."""
    return {
        "properties": [
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": "PROP-001"},
                    "Location": {
                        "Address": "1 High St",
                        "City": "London",
                        "County": "Greater London",
                        "Latitude": 51.5,
                        "Longitude": -0.1,
                    },
                }
            },
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": "PROP-002"},
                    "Location": {
                        "Address": "2 River Rd",
                        "City": "Oxford",
                        "County": "Oxfordshire",
                        "Latitude": 51.75,
                        "Longitude": -1.25,
                    },
                }
            },
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": "PROP-003"},
                    "Location": {
                        "Address": "3 Thames Walk",
                        "City": "Richmond",
                        "County": "Greater London",
                        "Latitude": 51.46,
                        "Longitude": -0.3,
                    },
                }
            },
        ]
    }


class TestFindByCounty:
    """Cover PropertyLoader.find_by_county() lines 164-175."""

    def test_find_by_county_exact_match(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", _property_json_with_counties())
        loader = PropertyLoader(tmp_path)
        results = loader.find_by_county("Oxfordshire")
        assert len(results) == 1
        assert results[0]["PropertyHeader"]["Header"]["PropertyID"] == "PROP-002"

    def test_find_by_county_partial_match(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", _property_json_with_counties())
        loader = PropertyLoader(tmp_path)
        results = loader.find_by_county("london")
        assert len(results) == 2
        ids = {r["PropertyHeader"]["Header"]["PropertyID"] for r in results}
        assert ids == {"PROP-001", "PROP-003"}

    def test_find_by_county_case_insensitive(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", _property_json_with_counties())
        loader = PropertyLoader(tmp_path)
        results = loader.find_by_county("OXFORDSHIRE")
        assert len(results) == 1

    def test_find_by_county_no_match(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", _property_json_with_counties())
        loader = PropertyLoader(tmp_path)
        results = loader.find_by_county("Surrey")
        assert results == []

    def test_find_by_county_empty_portfolio(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", {"properties": []})
        loader = PropertyLoader(tmp_path)
        results = loader.find_by_county("London")
        assert results == []

    def test_find_by_county_missing_county_field(self, tmp_path):
        """Property with no County field should not crash."""
        from loaders.property_loader import PropertyLoader
        data = {
            "properties": [
                {
                    "PropertyHeader": {
                        "Header": {"PropertyID": "PROP-X"},
                        "Location": {"Address": "No County Rd"},
                    }
                }
            ]
        }
        write_json(tmp_path / "property.json", data)
        loader = PropertyLoader(tmp_path)
        results = loader.find_by_county("London")
        assert results == []
