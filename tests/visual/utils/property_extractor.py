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
Tests for visual.utils.data_extractors.property_extractor.

Covers: extract_property_info, _calculate_age_factor,
_extract_property_value, and PropertyDataExtractor class.
"""

import pytest

from visual.utils.data_extractors.property_extractor import (
    extract_property_info,
    PropertyDataExtractor,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_prop(property_id="PROP-001", lat=51.5, lon=-0.1,
               year=2000, value=400_000):
    return {
        "PropertyHeader": {
            "Header": {
                "PropertyID": property_id,
                "propertyType": "Residential",
                "propertyStatus": "Active",
            },
            "PropertyAttributes": {
                "PropertyType": "Detached",
                "ConstructionYear": year,
                "NumberOfStoreys": 2,
            },
            "Construction": {
                "ConstructionType": "Brick",
                "FloorLevelMeters": 0.3,
            },
            "Location": {
                "LatitudeDegrees": lat,
                "LongitudeDegrees": lon,
                "BuildingNumber": "42",
                "StreetName": "Fleet Street",
                "TownCity": "London",
                "Postcode": "EC4Y 1BJ",
            },
            "Valuation": {"PropertyValue": value},
        },
        "FloodRisk": "Medium",
        "ThamesProximity": "0.5km",
        "GroundElevation": 5.0,
    }


# ===========================================================================
# extract_property_info
# ===========================================================================

class TestExtractPropertyInfo:

    def test_returns_dict_for_valid_property(self):
        result = extract_property_info(_make_prop())
        assert isinstance(result, dict)

    def test_extracts_property_id(self):
        result = extract_property_info(_make_prop(property_id="PROP-XYZ"))
        assert result["property_id"] == "PROP-XYZ"

    def test_extracts_coordinates(self):
        result = extract_property_info(_make_prop(lat=51.5, lon=-0.1))
        assert result["coordinates"]["latitude"] == pytest.approx(51.5)
        assert result["coordinates"]["longitude"] == pytest.approx(-0.1)

    def test_missing_lat_returns_none(self):
        prop = _make_prop()
        prop["PropertyHeader"]["Location"]["LatitudeDegrees"] = None
        prop["PropertyHeader"]["Location"].pop("Latitude", None)
        assert extract_property_info(prop) is None

    def test_missing_lon_returns_none(self):
        prop = _make_prop()
        prop["PropertyHeader"]["Location"]["LongitudeDegrees"] = None
        prop["PropertyHeader"]["Location"].pop("Longitude", None)
        assert extract_property_info(prop) is None

    def test_extracts_address(self):
        result = extract_property_info(_make_prop())
        addr = result["address"]
        assert addr["building_number"] == "42"
        assert addr["street_name"] == "Fleet Street"
        assert addr["town_city"] == "London"
        assert addr["post_code"] == "EC4Y 1BJ"

    def test_extracts_property_type(self):
        result = extract_property_info(_make_prop())
        assert result["property_type"] == "Residential"

    def test_extracts_construction_year(self):
        result = extract_property_info(_make_prop(year=1985))
        assert result["construction_year"] == 1985

    def test_age_factor_present(self):
        result = extract_property_info(_make_prop(year=1900))
        assert result["property_age_factor"] != "Unknown"
        assert "High Risk" in result["property_age_factor"]

    def test_modern_property_low_risk_age_factor(self):
        result = extract_property_info(_make_prop(year=2010))
        assert "Low Risk" in result["property_age_factor"]

    def test_property_value_extracted(self):
        result = extract_property_info(_make_prop(value=500_000))
        assert result["property_value"] == 500_000

    def test_latitude_alternative_key(self):
        prop = _make_prop()
        prop["PropertyHeader"]["Location"].pop("LatitudeDegrees")
        prop["PropertyHeader"]["Location"]["Latitude"] = 52.0
        result = extract_property_info(prop)
        assert result["coordinates"]["latitude"] == pytest.approx(52.0)

    def test_flood_risk_extracted(self):
        result = extract_property_info(_make_prop())
        assert result["flood_risk"] == "Medium"

    def test_property_value_from_top_level(self):
        prop = _make_prop(value=300_000)
        prop["PropertyValue"] = 999_999
        result = extract_property_info(prop)
        # Top-level PropertyValue takes precedence
        assert result["property_value"] == 999_999

    def test_property_value_unknown_when_missing(self):
        prop = _make_prop()
        prop["PropertyHeader"].pop("Valuation", None)
        result = extract_property_info(prop)
        assert result["property_value"] == "Unknown"


# ===========================================================================
# PropertyDataExtractor class
# ===========================================================================

class TestPropertyDataExtractor:

    def test_extract_property_info_delegates(self):
        extractor = PropertyDataExtractor()
        result = extractor.extract_property_info(_make_prop())
        assert result is not None
        assert result["property_id"] == "PROP-001"

    def test_extract_coordinates_returns_dict(self):
        extractor = PropertyDataExtractor()
        coords = extractor.extract_coordinates(_make_prop())
        assert "latitude" in coords
        assert "longitude" in coords

    def test_extract_coordinates_returns_none_for_missing(self):
        extractor = PropertyDataExtractor()
        prop = _make_prop()
        prop["PropertyHeader"]["Location"]["LatitudeDegrees"] = None
        prop["PropertyHeader"]["Location"].pop("Latitude", None)
        assert extractor.extract_coordinates(prop) is None

    def test_extract_address_returns_dict(self):
        extractor = PropertyDataExtractor()
        addr = extractor.extract_address(_make_prop())
        assert "street_name" in addr
        assert "town_city" in addr

    def test_extract_address_returns_none_for_invalid(self):
        extractor = PropertyDataExtractor()
        prop = _make_prop()
        prop["PropertyHeader"]["Location"]["LatitudeDegrees"] = None
        prop["PropertyHeader"]["Location"].pop("Latitude", None)
        assert extractor.extract_address(prop) is None
