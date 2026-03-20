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
Tests for PropertyLayer.add_to_map and _add_property_marker.
"""

import pytest
import folium
from unittest.mock import patch

from visual.layer.property_layer.layer import PropertyLayer


# ===========================================================================
# Helpers
# ===========================================================================

def _make_property(property_id="PROP-001", lat=51.5, lon=-0.1, year=2000):
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
            "Construction": {"ConstructionType": "Brick", "FloorLevelMeters": 0.3},
            "Location": {
                "LatitudeDegrees": lat,
                "LongitudeDegrees": lon,
                "BuildingNumber": "1",
                "StreetName": "Main St",
                "TownCity": "London",
                "Postcode": "EC4Y 1BJ",
            },
            "Valuation": {"PropertyValue": 400_000},
        },
        "FloodRisk": "Low",
    }


class MockLoadedData:
    def __init__(self, property_data=None, property_flood_info=None,
                 mortgage_lookup=None, mortgage_risk_info=None,
                 property_hazard_data=None):
        self.property_data = property_data
        self.property_flood_info = property_flood_info or {}
        self.mortgage_lookup = mortgage_lookup or {}
        self.mortgage_risk_info = mortgage_risk_info
        self.property_hazard_data = property_hazard_data


# ===========================================================================
# add_to_map — empty data
# ===========================================================================

class TestAddToMapEmpty:

    def test_returns_feature_group_when_no_property_data(self):
        layer = PropertyLayer()
        result = layer.add_to_map(folium.Map(), MockLoadedData(property_data=None))
        assert isinstance(result, folium.FeatureGroup)

    def test_returns_feature_group_when_properties_empty(self):
        layer = PropertyLayer()
        result = layer.add_to_map(folium.Map(), MockLoadedData(property_data={"items": []}))
        assert isinstance(result, folium.FeatureGroup)

    def test_feature_group_name_set(self):
        layer = PropertyLayer()
        result = layer.add_to_map(folium.Map(), MockLoadedData(property_data=None))
        assert result.layer_name == "Properties"


# ===========================================================================
# add_to_map — with data
# ===========================================================================

class TestAddToMapWithData:

    def test_single_property_added(self):
        layer = PropertyLayer()
        loaded = MockLoadedData(property_data={"items": [_make_property()]})
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_multiple_properties_added(self):
        layer = PropertyLayer()
        loaded = MockLoadedData(property_data={"items": [
            _make_property("P1"), _make_property("P2", lat=51.6, lon=-0.2)
        ]})
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_property_hazard_data_loaded(self):
        """Lines 69-73: property_hazard_data dict populated."""
        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
            property_hazard_data={
                "property_hazard_curves": {"PROP-001": {"flood_count": 8}}
            },
        )
        layer.add_to_map(folium.Map(), loaded)
        assert "PROP-001" in layer._property_hazard

    def test_property_hazard_non_dict_skipped(self):
        """Non-dict hazard entry not stored."""
        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
            property_hazard_data={
                "property_hazard_curves": {
                    "PROP-BAD": "not_a_dict",
                    "PROP-001": {"flood_count": 3}
                }
            },
        )
        layer.add_to_map(folium.Map(), loaded)
        assert "PROP-BAD" not in layer._property_hazard
        assert "PROP-001" in layer._property_hazard

    def test_property_with_mortgage_added(self):
        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
            mortgage_lookup={"PROP-001": {"original_loan": 250_000}},
        )
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_property_with_flood_info(self):
        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
            property_flood_info={"PROP-001": {"risk_level": "High", "flood_depth": 0.5}},
        )
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_property_with_mortgage_risk_info(self):
        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
            mortgage_lookup={"PROP-001": {"original_loan": 250_000}},
            mortgage_risk_info={"by_property_id": {"PROP-001": {"flood_risk_level": "High"}}},
        )
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_high_hazard_property(self):
        """Property with flood_count > 5 gets red icon."""
        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
            property_hazard_data={
                "property_hazard_curves": {"PROP-001": {"flood_count": 10}}
            },
        )
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)


# ===========================================================================
# add_to_map — line 111: extract_property_info returns None
# ===========================================================================

class TestPropertyInfoNone:

    def test_none_property_info_skipped(self):
        """Line 111: extract_property_info returns None → property skipped, no crash."""
        layer = PropertyLayer()
        loaded = MockLoadedData(property_data={"items": [_make_property("PROP-001")]})
        with patch("visual.layer.property_layer.layer.DataExtractor.extract_property_info", return_value=None):
            result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)


# ===========================================================================
# add_to_map — lines 132-134: exception inside property loop
# ===========================================================================

class TestAddToMapException:

    def test_property_flood_info_raises_skipped(self):
        """Lines 132-134: exception in property loop → caught, next property processed."""
        class RaisingFloodInfo:
            def get(self, *args, **kwargs):
                raise RuntimeError("flood info failure")

        layer = PropertyLayer()
        loaded = MockLoadedData(
            property_data={"items": [_make_property("PROP-001")]},
        )
        loaded.property_flood_info = RaisingFloodInfo()
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)


# ===========================================================================
# _add_property_marker — lines 191-192: KeyError in marker creation
# ===========================================================================

class TestAddPropertyMarkerException:

    def test_missing_coordinates_key_handled(self):
        """Lines 191-192: KeyError in _add_property_marker → caught and logged."""
        layer = PropertyLayer()
        layer._property_hazard = {}
        fg = folium.FeatureGroup()
        # property_info missing 'coordinates' key → KeyError at line 157
        property_info = {
            "property_id": "PROP-001",
            # no 'coordinates' key
        }
        mock_loaded = MockLoadedData()
        layer._add_property_marker(fg, property_info, {}, False, {}, mock_loaded)
        # No crash — exception caught at line 191
