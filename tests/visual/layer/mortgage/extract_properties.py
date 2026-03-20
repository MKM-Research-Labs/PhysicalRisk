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

"""
Tests for MortgageLayer._extract_mortgage_locations and _get_properties_list.
"""

import pytest
import folium

from visual.layer.mortgage_layer.layer import MortgageLayer


# ===========================================================================
# Helpers
# ===========================================================================

def _make_property(property_id="PROP-001", lat=51.5, lon=-0.1):
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": property_id},
            "Location": {"LatitudeDegrees": lat, "LongitudeDegrees": lon},
        }
    }


class MockLoadedData:
    def __init__(self, mortgage_data=None, property_data=None,
                 mortgage_lookup=None, mortgage_risk_info=None, property_flood_info=None):
        self.mortgage_data = mortgage_data
        self.property_data = property_data
        self.mortgage_lookup = mortgage_lookup or {}
        self.mortgage_risk_info = mortgage_risk_info
        self.property_flood_info = property_flood_info or {}


# ===========================================================================
# _extract_mortgage_locations
# ===========================================================================

class TestExtractMortgageLocations:

    def test_empty_lookup_returns_empty(self):
        layer = MortgageLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property()]}, mortgage_lookup={}
        )
        assert layer._extract_mortgage_locations(loaded) == []

    def test_none_lookup_returns_empty(self):
        """Lines 102-103: mortgage_lookup is None → empty list."""
        layer = MortgageLayer()
        loaded = MockLoadedData(property_data={"items": [_make_property()]})
        loaded.mortgage_lookup = None
        assert layer._extract_mortgage_locations(loaded) == []

    def test_mortgage_with_matching_property(self):
        layer = MortgageLayer()
        prop = _make_property("PROP-001", lat=51.5, lon=-0.1)
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 250_000}},
        )
        result = layer._extract_mortgage_locations(loaded)
        assert len(result) == 1
        assert result[0]["property_id"] == "PROP-001"
        assert result[0]["lat"] == pytest.approx(51.5)
        assert result[0]["lon"] == pytest.approx(-0.1)

    def test_mortgage_without_matching_property_skipped(self):
        layer = MortgageLayer()
        loaded = MockLoadedData(
            property_data={"items": []},
            mortgage_lookup={"PROP-X": {"original_loan": 100_000}},
        )
        assert layer._extract_mortgage_locations(loaded) == []

    def test_risk_info_attached_when_present(self):
        layer = MortgageLayer()
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 200_000}},
            mortgage_risk_info={
                "by_property_id": {"PROP-001": {"flood_risk_level": "High"}}
            },
        )
        result = layer._extract_mortgage_locations(loaded)
        assert result[0]["mortgage_risk_info"]["flood_risk_level"] == "High"

    def test_risk_info_none_when_not_by_property_id(self):
        """mortgage_risk_info without 'by_property_id' key → risk_info is None."""
        layer = MortgageLayer()
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 200_000}},
            mortgage_risk_info={"other_key": {}},
        )
        result = layer._extract_mortgage_locations(loaded)
        assert result[0]["mortgage_risk_info"] is None

    def test_property_flood_info_attached(self):
        layer = MortgageLayer()
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 200_000}},
            property_flood_info={"PROP-001": {"risk_level": "Medium"}},
        )
        result = layer._extract_mortgage_locations(loaded)
        assert result[0]["property_flood_info"]["risk_level"] == "Medium"

    def test_multiple_mortgages(self):
        layer = MortgageLayer()
        props = [_make_property("P1", lat=51.4, lon=-0.2),
                 _make_property("P2", lat=51.5, lon=-0.1)]
        loaded = MockLoadedData(
            property_data={"items": props},
            mortgage_lookup={"P1": {"original_loan": 200_000}, "P2": {"original_loan": 300_000}},
        )
        result = layer._extract_mortgage_locations(loaded)
        assert len(result) == 2

    def test_property_uses_latitude_alternative_key(self):
        """Location with 'Latitude' key (not 'LatitudeDegrees')."""
        layer = MortgageLayer()
        prop = {
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-ALT"},
                "Location": {"Latitude": 51.6, "Longitude": -0.2},
            }
        }
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-ALT": {"original_loan": 150_000}},
        )
        result = layer._extract_mortgage_locations(loaded)
        assert len(result) == 1
        assert result[0]["lat"] == pytest.approx(51.6)


# ===========================================================================
# _get_properties_list
# ===========================================================================

class TestGetPropertiesList:

    def test_items_key(self):
        layer = MortgageLayer()
        result = layer._get_properties_list({"items": [_make_property()]})
        assert len(result) == 1

    def test_properties_key(self):
        layer = MortgageLayer()
        result = layer._get_properties_list({"properties": [_make_property()]})
        assert len(result) == 1

    def test_property_header_single_item(self):
        """Dict with 'PropertyHeader' key → wrapped as single-item list."""
        layer = MortgageLayer()
        prop = _make_property()
        result = layer._get_properties_list(prop)
        assert len(result) == 1

    def test_portfolio_key_fallback(self):
        """Dict with no items/properties/PropertyHeader → uses 'portfolio' key."""
        layer = MortgageLayer()
        result = layer._get_properties_list({"portfolio": [_make_property()]})
        assert len(result) == 1

    def test_list_input(self):
        layer = MortgageLayer()
        result = layer._get_properties_list([_make_property()])
        assert len(result) == 1

    def test_empty_dict_returns_empty_list(self):
        layer = MortgageLayer()
        assert layer._get_properties_list({}) == []

    def test_empty_items_returns_empty_list(self):
        layer = MortgageLayer()
        assert layer._get_properties_list({"items": []}) == []


# ===========================================================================
# Additional TestExtractMortgageLocations — exception paths
# ===========================================================================

class TestExtractMortgageLocationsExceptions:

    def test_bad_lat_skipped(self):
        """Lines 139-140: float(lat) raises → property coordinate not stored → mortgage skipped."""
        layer = MortgageLayer()
        prop = {
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-BAD"},
                "Location": {"LatitudeDegrees": "not_a_number", "LongitudeDegrees": -0.1},
            }
        }
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-BAD": {"original_loan": 100_000}},
        )
        result = layer._extract_mortgage_locations(loaded)
        assert result == []

    def test_append_exception_skipped(self):
        """Lines 165-167: exception during mortgage append → skipped."""
        class RaisingFloodInfo:
            def get(self, *args, **kwargs):
                raise RuntimeError("flood info error")

        layer = MortgageLayer()
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 200_000}},
        )
        loaded.property_flood_info = RaisingFloodInfo()
        result = layer._extract_mortgage_locations(loaded)
        assert result == []


# ===========================================================================
# _get_properties_list — else branch (non-dict, non-list)
# ===========================================================================

class TestGetPropertiesListElseBranch:

    def test_non_dict_non_list_returns_empty(self):
        """Line 399: else branch — integer input returns empty list."""
        layer = MortgageLayer()
        assert layer._get_properties_list(42) == []
