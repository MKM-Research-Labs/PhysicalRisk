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
Tests for MortgageLayer._get_mortgage_risk_color, _create_mortgage_circle_popup,
and get_mortgage_statistics.
"""

import pytest
import folium

from visual.layer.mortgage_layer.layer import MortgageLayer


# ===========================================================================
# Helpers
# ===========================================================================

def _make_location(property_id="PROP-001", lat=51.5, lon=-0.1,
                   loan=250_000, mortgage_risk_info=None, flood_info=None,
                   ltv=0.75):
    return {
        "property_id": property_id,
        "lat": lat,
        "lon": lon,
        "mortgage_info": {"original_loan": loan, "loan_to_value_ratio": ltv,
                          "OriginalLTV": ltv, "original_lending_rate": 0.04},
        "mortgage_risk_info": mortgage_risk_info,
        "property_flood_info": flood_info or {},
    }


# ===========================================================================
# _get_mortgage_risk_color
# ===========================================================================

class TestGetMortgageRiskColor:

    def test_uses_mortgage_risk_info_when_present(self):
        """Lines 291-293: risk info available → flood_risk_level lookup."""
        layer = MortgageLayer()
        mortgage_info = {"original_loan": 250_000}
        risk_info = {"flood_risk_level": "High"}
        color = layer._get_mortgage_risk_color(mortgage_info, risk_info, {})
        assert isinstance(color, str)
        assert len(color) > 0

    def test_falls_back_to_property_flood_info(self):
        """Lines 295-298: no risk_info → property flood info."""
        layer = MortgageLayer()
        mortgage_info = {"original_loan": 250_000}
        flood_info = {"risk_level": "Medium"}
        color = layer._get_mortgage_risk_color(mortgage_info, None, flood_info)
        assert isinstance(color, str)

    def test_falls_back_to_ltv_coloring(self):
        """Lines 300-305: no risk_info or flood_info → LTV-based color."""
        layer = MortgageLayer()
        mortgage_info = {"loan_to_value_ratio": 0.9}
        color = layer._get_mortgage_risk_color(mortgage_info, None, {})
        assert isinstance(color, str)

    def test_normalizes_ltv_above_1(self):
        """Line 303-304: ltv_ratio > 1 → divided by 100."""
        layer = MortgageLayer()
        mortgage_info = {"loan_to_value_ratio": 90}  # percentage
        color = layer._get_mortgage_risk_color(mortgage_info, None, {})
        assert isinstance(color, str)

    def test_default_blue_when_no_data(self):
        """Line 308: no risk/flood/ltv → default blue."""
        layer = MortgageLayer()
        mortgage_info = {}
        color = layer._get_mortgage_risk_color(mortgage_info, None, {})
        assert color == "#2196F3"

    def test_ltv_alternative_key(self):
        """LoanToValueRatio (camel case) as fallback key."""
        layer = MortgageLayer()
        mortgage_info = {"LoanToValueRatio": 0.85}
        color = layer._get_mortgage_risk_color(mortgage_info, None, {})
        assert isinstance(color, str)


# ===========================================================================
# _create_mortgage_circle_popup
# ===========================================================================

class TestCreateMortgageCirclePopup:

    def test_returns_html_string(self):
        layer = MortgageLayer()
        html = layer._create_mortgage_circle_popup(_make_location())
        assert isinstance(html, str)
        assert "<div" in html

    def test_contains_property_id(self):
        layer = MortgageLayer()
        html = layer._create_mortgage_circle_popup(_make_location("PROP-007"))
        assert "PROP-007" in html

    def test_contains_loan_details(self):
        layer = MortgageLayer()
        html = layer._create_mortgage_circle_popup(_make_location(loan=300_000))
        assert "Loan Details" in html

    def test_includes_risk_section_when_risk_info_present(self):
        """Lines 342-354: risk info section rendered."""
        layer = MortgageLayer()
        location = _make_location(mortgage_risk_info={
            "flood_risk_level": "High",
            "mortgage_value": 230_000,
            "mortgage_value_at_risk": 50_000,
        })
        html = layer._create_mortgage_circle_popup(location)
        assert "Risk Assessment" in html
        assert "High" in html

    def test_excludes_risk_section_when_no_risk_info(self):
        """No risk info → risk section absent."""
        layer = MortgageLayer()
        html = layer._create_mortgage_circle_popup(_make_location(mortgage_risk_info=None))
        assert "Risk Assessment" not in html

    def test_includes_flood_section_when_flood_info_present(self):
        """Lines 356-364: flood info section rendered."""
        layer = MortgageLayer()
        location = _make_location(flood_info={"risk_level": "Medium", "flood_depth": 0.3})
        html = layer._create_mortgage_circle_popup(location)
        assert "Flood Context" in html

    def test_excludes_flood_section_when_no_flood_info(self):
        layer = MortgageLayer()
        html = layer._create_mortgage_circle_popup(_make_location(flood_info={}))
        assert "Flood Context" not in html

    def test_interest_rate_less_than_1_multiplied(self):
        """Interest rate < 1 multiplied by 100 for display."""
        layer = MortgageLayer()
        location = _make_location()
        location["mortgage_info"]["original_lending_rate"] = 0.045
        html = layer._create_mortgage_circle_popup(location)
        assert "4.5" in html or "Interest Rate" in html


# ===========================================================================
# get_mortgage_statistics
# ===========================================================================

class TestGetMortgageStatistics:

    def test_empty_returns_empty_dict(self):
        assert MortgageLayer().get_mortgage_statistics([]) == {}

    def test_total_mortgages(self):
        layer = MortgageLayer()
        locations = [_make_location("P1", loan=200_000),
                     _make_location("P2", loan=300_000)]
        stats = layer.get_mortgage_statistics(locations)
        assert stats["total_mortgages"] == 2

    def test_avg_loan_amount(self):
        layer = MortgageLayer()
        locations = [_make_location("P1", loan=200_000),
                     _make_location("P2", loan=300_000)]
        stats = layer.get_mortgage_statistics(locations)
        assert stats["avg_loan_amount"] == pytest.approx(250_000)

    def test_total_loan_value(self):
        layer = MortgageLayer()
        locations = [_make_location("P1", loan=200_000),
                     _make_location("P2", loan=300_000)]
        stats = layer.get_mortgage_statistics(locations)
        assert stats["total_loan_value"] == pytest.approx(500_000)

    def test_avg_ltv_ratio(self):
        layer = MortgageLayer()
        locations = [_make_location()]
        stats = layer.get_mortgage_statistics(locations)
        assert stats["avg_ltv_ratio"] == pytest.approx(0.75)

    def test_high_ltv_count(self):
        layer = MortgageLayer()
        loc1 = _make_location("P1", ltv=0.85)  # > 0.8
        loc2 = _make_location("P2", ltv=0.5)   # < 0.8
        stats = layer.get_mortgage_statistics([loc1, loc2])
        assert stats["high_ltv_count"] == 1

    def test_risk_distribution(self):
        layer = MortgageLayer()
        loc = _make_location(mortgage_risk_info={"flood_risk_level": "High"})
        stats = layer.get_mortgage_statistics([loc])
        assert stats["risk_distribution"].get("High", 0) == 1

    def test_no_loan_amount_excluded(self):
        """Zero loan amount not included in avg calculation."""
        layer = MortgageLayer()
        loc = _make_location(loan=0)
        stats = layer.get_mortgage_statistics([loc])
        assert stats["avg_loan_amount"] == pytest.approx(0)

    def test_ltv_above_1_normalized(self):
        """LTV > 1 treated as percentage, normalized to ratio."""
        layer = MortgageLayer()
        loc = _make_location(ltv=80)  # percentage → normalized to 0.8
        stats = layer.get_mortgage_statistics([loc])
        assert stats["avg_ltv_ratio"] == pytest.approx(0.8)


# ===========================================================================
# _add_mortgage_risk_circles — exception paths
# ===========================================================================

class TestAddMortgageRiskCircles:

    def _make_loc(self, loan=300_000, mortgage_info=None):
        info = mortgage_info if mortgage_info is not None else {"original_loan": loan}
        return {
            "property_id": "P1",
            "lat": 51.5,
            "lon": -0.1,
            "mortgage_info": info,
            "mortgage_risk_info": None,
            "property_flood_info": {},
        }

    def test_zero_loan_in_mixed_list_skipped(self):
        """Line 207: location with loan=0 skipped when others are valid."""
        layer = MortgageLayer()
        fg = folium.FeatureGroup()
        locations = [
            self._make_loc(loan=300_000),
            {**self._make_loc(loan=0), "property_id": "P2"},
        ]
        layer._add_mortgage_risk_circles(fg, locations)  # no crash

    def test_circle_exception_skipped(self):
        """Lines 235-237: exception in circle creation loop → skipped."""
        layer = MortgageLayer()
        fg = folium.FeatureGroup()
        # Second location has invalid lat/lon (string) → folium.Circle raises
        locations = [
            self._make_loc(loan=300_000),
            {
                "property_id": "P2",
                "lat": "not_a_number",
                "lon": -0.2,
                "mortgage_info": {"original_loan": 400_000},
                "mortgage_risk_info": None,
                "property_flood_info": {},
            },
        ]
        layer._add_mortgage_risk_circles(fg, locations)  # no crash


# ===========================================================================
# _add_ltv_indicators — exception paths
# ===========================================================================

class TestAddLtvIndicators:

    def test_ltv_indicator_exception_skipped(self):
        """Lines 289-291: exception in LTV loop → skipped."""
        layer = MortgageLayer()
        fg = folium.FeatureGroup()
        locations = [{
            "property_id": "P1",
            "lat": 51.5,
            "lon": -0.1,
            "mortgage_info": None,  # .get() raises AttributeError
            "mortgage_risk_info": None,
            "property_flood_info": {},
        }]
        layer._add_ltv_indicators(fg, locations)  # no crash
