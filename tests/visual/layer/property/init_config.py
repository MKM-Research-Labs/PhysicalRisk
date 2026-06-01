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
Tests for PropertyLayer.__init__, configure, and get_property_statistics.
"""

import pytest
import folium

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
                 rloan_lookup=None,
                 property_hazard_data=None):
        self.property_data = property_data
        self.property_flood_info = property_flood_info or {}
        self.rloan_lookup = rloan_lookup or {}
        self.property_hazard_data = property_hazard_data


# ===========================================================================
# __init__
# ===========================================================================

class TestPropertyLayerInit:

    def test_layer_name(self):
        assert PropertyLayer().layer_name == "Properties"

    def test_show_risk_colors_default(self):
        assert PropertyLayer().show_risk_colors is True

    def test_show_mortgage_status_default(self):
        assert PropertyLayer().show_rloan_status is True

    def test_risk_based_sizing_default(self):
        assert PropertyLayer().risk_based_sizing is False


# ===========================================================================
# configure
# ===========================================================================

class TestConfigure:

    def test_configure_all_params(self):
        layer = PropertyLayer()
        layer.configure(show_risk_colors=False, show_rloan_status=False,
                        risk_based_sizing=True)
        assert layer.show_risk_colors is False
        assert layer.show_rloan_status is False
        assert layer.risk_based_sizing is True

    def test_configure_defaults(self):
        layer = PropertyLayer()
        layer.configure()
        assert layer.show_risk_colors is True
        assert layer.show_rloan_status is True
        assert layer.risk_based_sizing is False

    def test_configure_partial(self):
        layer = PropertyLayer()
        layer.configure(show_rloan_status=False)
        assert layer.show_risk_colors is True
        assert layer.show_rloan_status is False


# ===========================================================================
# get_property_statistics
# ===========================================================================

class TestGetPropertyStatistics:

    def test_empty_properties_returns_empty_dict(self):
        layer = PropertyLayer()
        loaded = MockLoadedData()
        assert layer.get_property_statistics([], loaded) == {}

    def test_total_properties(self):
        layer = PropertyLayer()
        layer._property_hazard = {}
        props = [_make_property("P1"), _make_property("P2")]
        loaded = MockLoadedData()
        stats = layer.get_property_statistics(props, loaded)
        assert stats["total_properties"] == 2

    def test_mortgaged_count(self):
        layer = PropertyLayer()
        layer._property_hazard = {}
        props = [_make_property("P1"), _make_property("P2")]
        loaded = MockLoadedData(rloan_lookup={"P1": {}})
        stats = layer.get_property_statistics(props, loaded)
        assert stats["mortgaged_properties"] == 1

    def test_mortgage_percentage(self):
        layer = PropertyLayer()
        layer._property_hazard = {}
        props = [_make_property("P1"), _make_property("P2")]
        loaded = MockLoadedData(rloan_lookup={"P1": {}})
        stats = layer.get_property_statistics(props, loaded)
        assert stats["mortgage_percentage"] == pytest.approx(50.0)

    def test_risk_distribution(self):
        layer = PropertyLayer()
        layer._property_hazard = {}
        props = [_make_property("P1"), _make_property("P2")]
        loaded = MockLoadedData(
            property_flood_info={"P1": {"risk_level": "High"}, "P2": {"risk_level": "Low"}}
        )
        stats = layer.get_property_statistics(props, loaded)
        assert isinstance(stats["risk_distribution"], dict)
