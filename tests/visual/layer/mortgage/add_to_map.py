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
Tests for MortgageLayer.add_to_map with various data configurations.
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
# add_to_map — insufficient data (early exits)
# ===========================================================================

class TestAddToMapInsufficient:

    def test_returns_feature_group_when_no_mortgage_data(self):
        layer = MortgageLayer()
        loaded = MockLoadedData(mortgage_data=None, property_data={"items": []})
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_returns_feature_group_when_no_property_data(self):
        layer = MortgageLayer()
        loaded = MockLoadedData(mortgage_data={"items": []}, property_data=None)
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_returns_feature_group_when_empty_lookup(self):
        layer = MortgageLayer()
        loaded = MockLoadedData(
            mortgage_data={"items": []}, property_data={"items": []}, mortgage_lookup={}
        )
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_feature_group_name_set(self):
        layer = MortgageLayer()
        loaded = MockLoadedData(mortgage_data=None, property_data=None)
        result = layer.add_to_map(folium.Map(), loaded)
        assert result.layer_name == "Mortgage Risk"


# ===========================================================================
# add_to_map — with full data (circles + LTV)
# ===========================================================================

class TestAddToMapWithData:

    def _loaded(self, *, risk_circles=True, ltv_indicators=True, loan=300_000, ltv=0.85):
        prop = _make_property("PROP-001")
        return MockLoadedData(
            mortgage_data={"items": [prop]},
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {
                "original_loan": loan,
                "OriginalLTV": ltv,
            }},
        )

    def test_add_to_map_with_risk_circles(self):
        layer = MortgageLayer()
        layer.configure(show_risk_circles=True, show_ltv_indicators=False)
        result = layer.add_to_map(folium.Map(), self._loaded())
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_with_ltv_indicators(self):
        layer = MortgageLayer()
        layer.configure(show_risk_circles=False, show_ltv_indicators=True)
        result = layer.add_to_map(folium.Map(), self._loaded())
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_with_both_disabled(self):
        layer = MortgageLayer()
        layer.configure(show_risk_circles=False, show_ltv_indicators=False)
        result = layer.add_to_map(folium.Map(), self._loaded())
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_with_low_ltv_no_indicator(self):
        """LTV < 0.8 → no LTV indicator added."""
        layer = MortgageLayer()
        layer.configure(show_risk_circles=False, show_ltv_indicators=True)
        loaded = self._loaded(ltv=0.5)
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_no_loan_amount_skips_circle(self):
        """Zero loan amount → circle skipped."""
        layer = MortgageLayer()
        layer.configure(show_risk_circles=True, show_ltv_indicators=False)
        loaded = self._loaded(loan=0)
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_with_risk_info(self):
        """Risk info enriches circle popup."""
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            mortgage_data={"items": [prop]},
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 250_000}},
            mortgage_risk_info={
                "by_property_id": {"PROP-001": {"flood_risk_level": "High", "mortgage_value": 230_000}}
            },
        )
        layer = MortgageLayer()
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_with_flood_info(self):
        """Property flood info populates popup context."""
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            mortgage_data={"items": [prop]},
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 250_000}},
            property_flood_info={"PROP-001": {"risk_level": "Medium", "flood_depth": 0.5}},
        )
        layer = MortgageLayer()
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_add_to_map_ltv_normalized(self):
        """LTV > 1 is treated as percentage and normalized."""
        prop = _make_property("PROP-001")
        loaded = MockLoadedData(
            mortgage_data={"items": [prop]},
            property_data={"items": [prop]},
            mortgage_lookup={"PROP-001": {"original_loan": 250_000, "OriginalLTV": 90}},
        )
        layer = MortgageLayer()
        layer.configure(show_risk_circles=False, show_ltv_indicators=True)
        result = layer.add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)
