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

"""Tests for visual.layer.commercial_layer.CommercialLayer.

Covers: per-type icon selection, marker placement, layer no-ops on
missing data, loan linkage by PropertyID, and the stats summary.
"""

from types import SimpleNamespace

import folium
import pytest

from visual.layer import CommercialLayer
from visual.layer.commercial_layer.layer import _ICON_BY_TYPE, _MARKER_COLOR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _asset(pid: str = "CPROP-1", ctype: str = "Office", lat: float = 51.5,
           lon: float = -0.1, value: float = 50_000_000, area: float = 5000,
           storeys: int = 10, town: str = "London") -> dict:
    return {
        "CommercialAsset": {
            "Header": {"PropertyID": pid, "CatchmentID": "thames"},
            "Valuation": {"PropertyValue": value},
            "CommercialAttributes": {
                "CommercialType": ctype,
                "PropertyAreaSqm": area,
                "NumberOfStoreys": storeys,
                "OccupancyStatus": "Fully occupied",
                "UseClassUKO": "E(g)(i)",
            },
            "Location": {
                "LatitudeDegrees": lat, "LongitudeDegrees": lon,
                "BuildingNumber": "12", "StreetName": "Test St",
                "TownCity": town, "Postcode": "SW1A 1AA",
            },
        }
    }


def _loaded(*assets, loan_lookup=None) -> SimpleNamespace:
    return SimpleNamespace(
        commercial_data={"commercial_assets": list(assets)},
        commercial_loan_lookup=loan_lookup or {},
    )


def _marker_popup_html(group: folium.FeatureGroup) -> str:
    """Extract the rendered popup HTML from the first Marker in a FeatureGroup.

    Folium attaches the Popup as a child of the Marker rather than an
    attribute, so we walk the marker's _children dict to find it.
    """
    marker = next(c for c in group._children.values() if isinstance(c, folium.Marker))
    popup = next(c for c in marker._children.values() if isinstance(c, folium.Popup))
    return popup.html.render()


# ---------------------------------------------------------------------------
# add_to_map
# ---------------------------------------------------------------------------


class TestAddToMap:

    def test_returns_feature_group(self):
        layer = CommercialLayer()
        result = layer.add_to_map(folium.Map(), _loaded(_asset()))
        assert isinstance(result, folium.FeatureGroup)

    def test_layer_name(self):
        assert CommercialLayer().layer_name == "Commercial Assets"

    def test_no_commercial_data_returns_empty_group(self):
        loaded = SimpleNamespace(commercial_data=None, commercial_loan_lookup={})
        result = CommercialLayer().add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_empty_commercial_assets_returns_empty_group(self):
        loaded = SimpleNamespace(commercial_data={"commercial_assets": []},
                                  commercial_loan_lookup={})
        result = CommercialLayer().add_to_map(folium.Map(), loaded)
        assert isinstance(result, folium.FeatureGroup)

    def test_marker_count_matches_assets(self):
        layer = CommercialLayer()
        loaded = _loaded(_asset("CPROP-1"), _asset("CPROP-2"), _asset("CPROP-3"))
        group = layer.add_to_map(folium.Map(), loaded)
        # FeatureGroup stores children in _children dict
        markers = [c for c in group._children.values() if isinstance(c, folium.Marker)]
        assert len(markers) == 3

    def test_asset_without_lat_lon_skipped(self):
        bad = _asset("CPROP-bad")
        bad["CommercialAsset"]["Location"]["LatitudeDegrees"] = None
        bad["CommercialAsset"]["Location"]["LongitudeDegrees"] = None
        group = CommercialLayer().add_to_map(folium.Map(), _loaded(bad))
        markers = [c for c in group._children.values() if isinstance(c, folium.Marker)]
        assert len(markers) == 0


# ---------------------------------------------------------------------------
# Icon selection per CommercialType
# ---------------------------------------------------------------------------


class TestIconByType:

    @pytest.mark.parametrize("ctype, expected_icon", [
        ("Office", "briefcase"),
        ("MultiFamily", "building"),
        ("Hotel", "hotel"),
        ("Retail", "shopping-cart"),
        ("Leisure", "glass-cheers"),
        ("Healthcare", "hospital"),
        ("MixedUse", "city"),
    ])
    def test_icon_per_type(self, ctype, expected_icon):
        assert _ICON_BY_TYPE[ctype] == expected_icon

    def test_marker_color_is_purple(self):
        # Purple distinguishes commercial from residential (green/orange/red)
        # and gauges (blue).
        assert _MARKER_COLOR == "purple"

    def test_unknown_type_falls_back_to_industry(self):
        layer = CommercialLayer()
        a = _asset("CPROP-x", ctype="UnknownType")
        group = layer.add_to_map(folium.Map(), _loaded(a))
        markers = [c for c in group._children.values() if isinstance(c, folium.Marker)]
        # Should still place a marker (with the fallback icon).
        assert len(markers) == 1


# ---------------------------------------------------------------------------
# Loan linkage
# ---------------------------------------------------------------------------


def _loan(property_id: str = "CPROP-1", loan_id: str = "CLOAN-aabb1122") -> dict:
    return {
        "Mortgage": {
            "Header": {"MortgageID": loan_id, "PropertyID": property_id},
            "Application": {"MortgageProvider": "Bank Of Test"},
            "FinancialTerms": {
                "OriginalLoan": 30_000_000,
                "OriginalLTV": 0.60,
                "OriginalLendingRate": 0.05,
                "OriginalTerm": 120,
            },
            "Features": {"RepaymentType": "Interest only"},
            "CurrentStatus": {"OutstandingBalance": 30_000_000},
        }
    }


class TestLoanLinkage:

    def test_loan_section_appears_in_popup(self):
        layer = CommercialLayer()
        loaded = _loaded(_asset("CPROP-1"), loan_lookup={"CPROP-1": _loan("CPROP-1")})
        group = layer.add_to_map(folium.Map(), loaded)
        html = _marker_popup_html(group)
        assert "Loan" in html
        assert "CLOAN-aabb1122" in html
        assert "Bank Of Test" in html

    def test_no_loan_section_when_unlinked(self):
        layer = CommercialLayer()
        loaded = _loaded(_asset("CPROP-1"), loan_lookup={})
        group = layer.add_to_map(folium.Map(), loaded)
        html = _marker_popup_html(group)
        # The Loan section's loan-id field is the unambiguous tell.
        assert "CLOAN-" not in html


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:

    def test_total_assets(self):
        layer = CommercialLayer()
        loaded = _loaded(_asset("CPROP-1"), _asset("CPROP-2", ctype="Hotel"))
        s = layer.get_commercial_statistics(loaded)
        assert s["total_assets"] == 2

    def test_per_type_count(self):
        layer = CommercialLayer()
        loaded = _loaded(
            _asset("CPROP-1", ctype="Office"),
            _asset("CPROP-2", ctype="Office"),
            _asset("CPROP-3", ctype="Hotel"),
        )
        s = layer.get_commercial_statistics(loaded)
        assert s["by_type_count"] == {"Office": 2, "Hotel": 1}

    def test_total_value(self):
        layer = CommercialLayer()
        loaded = _loaded(
            _asset("CPROP-1", value=10_000_000),
            _asset("CPROP-2", value=25_000_000),
        )
        s = layer.get_commercial_statistics(loaded)
        assert s["total_value_gbp"] == 35_000_000


# ---------------------------------------------------------------------------
# Popup content
# ---------------------------------------------------------------------------


class TestPopupContent:

    def _render(self, asset, loan=None):
        layer = CommercialLayer()
        loaded = _loaded(asset, loan_lookup={asset["CommercialAsset"]["Header"]["PropertyID"]: loan} if loan else {})
        group = layer.add_to_map(folium.Map(), loaded)
        return _marker_popup_html(group)

    def test_property_id_in_popup(self):
        html = self._render(_asset("CPROP-id001"))
        assert "CPROP-id001" in html

    def test_commercial_type_in_popup(self):
        html = self._render(_asset("CPROP-1", ctype="Hotel"))
        assert "Hotel" in html

    def test_address_in_popup(self):
        html = self._render(_asset("CPROP-1", town="Westminster"))
        assert "Westminster" in html

    def test_storeys_in_popup(self):
        html = self._render(_asset("CPROP-1", storeys=22))
        assert "22" in html

    def test_capital_value_in_popup(self):
        html = self._render(_asset("CPROP-1", value=12_000_000))
        # currency-formatted value
        assert "12,000,000" in html or "£12" in html
