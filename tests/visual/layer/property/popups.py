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
Tests for PropertyLayer popup methods:
_create_property_popup, _create_flood_risk_section,
_create_mortgage_section, _create_mortgage_risk_section.
"""

import pytest

from visual.layer.property_layer.layer import PropertyLayer


# ===========================================================================
# Helpers
# ===========================================================================

def _make_property_info(property_id="PROP-001", lat=51.5, lon=-0.1,
                         river_dist=200, ground_elevation=3.5):
    return {
        "property_id": property_id,
        "coordinates": {"latitude": lat, "longitude": lon},
        "address": {
            "street": "Main St",
            "city": "London",
            "postcode": "EC1A 1BB",
            "post_code": "EC1A 1BB",
        },
        "valuation": {"current_value": 500_000},
        "ground_elevation": ground_elevation,
        "floor_level_m": 0.5,
        "flood_zone": "2",
        "river_distance_m": river_dist,
        "property_type": "Detached",
        "building_type": "House",
        "construction_type": "Brick",
        "construction_year": 2000,
        "number_of_storeys": 2,
    }


def _make_mortgage_info(loan=250_000, rate=0.04, term=25, provider="Test Bank", ltv=None):
    info = {
        "original_loan": loan,
        "original_lending_rate": rate,
        "term_years": term,
        "mortgage_provider": provider,
    }
    if ltv is not None:
        info["loan_to_value_ratio"] = ltv
    return info


# ===========================================================================
# _create_property_popup
# ===========================================================================

class TestCreatePropertyPopup:

    def test_returns_html_string(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(), {}, False, {}, None)
        assert isinstance(html, str)
        assert "<div" in html

    def test_contains_property_id(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info("PROP-007"), {}, False, {}, None)
        assert "PROP-007" in html

    def test_contains_address(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(), {}, False, {}, None)
        assert "Main St" in html

    def test_contains_property_details_section(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(), {}, False, {}, None)
        assert "Property Details" in html
        assert "Detached" in html

    def test_coordinates_formatted(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(lat=51.5, lon=-0.1), {}, False, {}, None)
        assert "51.5" in html

    def test_coords_none_shows_na(self):
        """lat/lon both None → coord_str = 'N/A'."""
        layer = PropertyLayer()
        info = _make_property_info()
        info["coordinates"] = {"latitude": None, "longitude": None}
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "N/A" in html

    def test_river_distance_formatted(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(river_dist=300), {}, False, {}, None)
        assert "300" in html

    def test_river_distance_na_string(self):
        """river_dist = 'N/A' → shown as 'N/A'."""
        layer = PropertyLayer()
        info = _make_property_info()
        info["river_distance_m"] = "N/A"
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "N/A" in html

    def test_river_distance_none(self):
        """river_dist = None → shown as 'N/A'."""
        layer = PropertyLayer()
        info = _make_property_info()
        info["river_distance_m"] = None
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "N/A" in html

    def test_mortgage_section_included_when_has_mortgage(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(
            _make_property_info(), {}, True, _make_mortgage_info(), None
        )
        assert "MORTGAGE DETAILS" in html

    def test_mortgage_section_excluded_when_no_mortgage(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(), {}, False, {}, None)
        assert "MORTGAGE DETAILS" not in html

    def test_elevation_section(self):
        layer = PropertyLayer()
        html = layer._create_property_popup(_make_property_info(ground_elevation=4.5), {}, False, {}, None)
        assert "Elevation" in html

    def test_valuation_current_value(self):
        layer = PropertyLayer()
        info = _make_property_info()
        html = layer._create_property_popup(info, {}, False, {}, None)
        assert "Current Value" in html


# ===========================================================================
# _create_flood_risk_section
# ===========================================================================

class TestCreateFloodRiskSection:

    def test_returns_html_string(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({
            "risk_level": "High", "property_elevation": 4.0,
            "water_level": 5.0, "flood_depth": 1.0, "value_at_risk": 50_000,
        })
        assert isinstance(section, str)
        assert "<div" in section

    def test_includes_risk_level(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({"risk_level": "High"})
        assert "High" in section

    def test_empty_flood_info(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({})
        assert isinstance(section, str)
        assert "Unknown" in section

    def test_includes_flood_assessment_section(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({"risk_level": "Low"})
        assert "Flood Risk Assessment" in section

    def test_numeric_values_formatted(self):
        layer = PropertyLayer()
        section = layer._create_flood_risk_section({
            "risk_level": "Medium", "flood_depth": 0.75, "value_at_risk": 25_000
        })
        assert "0.75" in section


# ===========================================================================
# _create_mortgage_section
# ===========================================================================

class TestCreateMortgageSection:

    def test_returns_html_string(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(), 500_000)
        assert isinstance(html, str)
        assert "MORTGAGE DETAILS" in html

    def test_contains_lender(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(provider="Barclays"), 500_000)
        assert "Barclays" in html

    def test_interest_rate_less_than_1_multiplied(self):
        """Rate < 1 → displayed as percentage (4.0%)."""
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(rate=0.04), 500_000)
        assert "4.0" in html

    def test_interest_rate_above_1_used_directly(self):
        """Rate >= 1 → used as-is."""
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(rate=4.5), 500_000)
        assert "4.5" in html

    def test_ltv_calculated_from_loan_and_value(self):
        """LTV ratio computed from loan_amount / property_value."""
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(loan=250_000), 500_000)
        assert "50" in html or "LTV" in html

    def test_ltv_division_error_uses_fallback(self):
        """Division error (property_value=0) → falls back to mortgage info."""
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(), 0)
        assert isinstance(html, str)

    def test_alternative_keys(self):
        """OriginalLoan / OriginalLendingRate / TermYears / MortgageProvider keys."""
        layer = PropertyLayer()
        mortgage_info = {
            "OriginalLoan": 200_000,
            "OriginalLendingRate": 0.035,
            "TermYears": 20,
            "MortgageProvider": "NatWest",
        }
        html = layer._create_mortgage_section(mortgage_info, 400_000)
        assert "NatWest" in html

    def test_term_years_shown(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_section(_make_mortgage_info(term=30), 500_000)
        assert "30" in html

    def test_non_numeric_loan_amount_uses_fallback(self):
        """Lines 296-297: float(loan_amount) raises ValueError → fallback to mortgage_info LTV."""
        layer = PropertyLayer()
        mortgage_info = {"original_loan": "not_a_number", "loan_to_value_ratio": 0.5}
        html = layer._create_mortgage_section(mortgage_info, 500_000)
        assert isinstance(html, str)


# ===========================================================================
# _create_mortgage_risk_section
# ===========================================================================

class TestCreateMortgageRiskSection:

    def _risk_info(self, flood_risk="High", mortgage_value=230_000,
                   loan_amount=250_000, property_value=500_000, flood_depth=0.5):
        return {
            "flood_risk_level": flood_risk,
            "mortgage_value": mortgage_value,
            "loan_amount": loan_amount,
            "property_value": property_value,
            "mortgage_value_at_risk": 50_000,
            "flood_depth": flood_depth,
        }

    def test_returns_html_string(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_risk_section(self._risk_info())
        assert isinstance(html, str)
        assert "MORTGAGE RISK ANALYSIS" in html

    def test_includes_flood_risk_level(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_risk_section(self._risk_info(flood_risk="High"))
        assert "High" in html

    def test_includes_mortgage_value(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_risk_section(self._risk_info(mortgage_value=230_000))
        assert "Mortgage Value" in html

    def test_includes_risk_assessment(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_risk_section(self._risk_info())
        assert "Risk Assessment" in html

    def test_zero_property_value_no_crash(self):
        """property_value=0 → ltv_ratio = 0 (no ZeroDivision)."""
        layer = PropertyLayer()
        html = layer._create_mortgage_risk_section(self._risk_info(property_value=0))
        assert isinstance(html, str)

    def test_low_risk_level(self):
        layer = PropertyLayer()
        html = layer._create_mortgage_risk_section(self._risk_info(flood_risk="Low"))
        assert "Low" in html
