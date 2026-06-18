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

"""Tests for port.rand.thames.mortgage_random — financial data functions."""

import random

import pytest
from port.rand.thames.mortgage.mortgage_random import (
    determine_mortgage_type,
    calculate_mortgage_financials,
    estimate_property_value,
    generate_financial_data,
    _determine_occupancy_type,
)


# =============================================================================
# Helpers
# =============================================================================

def _financials(mortgage_type="Residential", property_value=400000):
    return calculate_mortgage_financials(property_value, mortgage_type, {})


# =============================================================================
# determine_mortgage_type
# =============================================================================

class TestDetermineMortgageType:

    def test_rental_income_returns_btl_or_residential(self):
        result = determine_mortgage_type({"monthly_rent": 1200})
        assert result in ["Buy-to-Let", "Residential"]

    def test_rental_history_returns_btl_or_residential(self):
        result = determine_mortgage_type({"rental_history": "Previously rented"})
        assert result in ["Buy-to-Let", "Residential"]

    def test_multi_family_returns_btl_or_residential(self):
        result = determine_mortgage_type({"building_residency": "Multi Family Residential"})
        assert result in ["Buy-to-Let", "Residential"]

    def test_vacant_property(self):
        result = determine_mortgage_type({"occupancy_type": "vacant"})
        assert result in ["Buy-to-Let", "Second Home", "Residential"]

    def test_empty_property_info_returns_valid(self):
        result = determine_mortgage_type({})
        assert result in ["Residential", "Buy-to-Let", "Second Home", "Holiday Home", "Shared Ownership"]


# =============================================================================
# calculate_mortgage_financials
# =============================================================================

class TestCalculateMortgageFinancials:

    def test_returns_dict(self):
        result = calculate_mortgage_financials(400000, "Residential", {})
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        result = calculate_mortgage_financials(400000, "Residential", {})
        for key in ("loan_amount", "outstanding_balance", "interest_rate", "monthly_payment", "ltv_ratio"):
            assert key in result

    def test_buy_to_let_type(self):
        result = calculate_mortgage_financials(300000, "Buy-to-Let", {})
        assert result["mortgage_type"] == "Buy-to-Let"

    def test_second_home_type(self):
        result = calculate_mortgage_financials(300000, "Second Home", {})
        assert result["mortgage_type"] == "Second Home"

    def test_high_flood_risk_reduces_ltv(self):
        random.seed(99)
        normal = calculate_mortgage_financials(400000, "Residential", {})
        random.seed(99)
        high_risk = calculate_mortgage_financials(400000, "Residential", {"flood_risk": "High"})
        assert high_risk["ltv_ratio"] <= normal["ltv_ratio"] + 0.01

    def test_loan_amount_positive(self):
        result = calculate_mortgage_financials(500000, "Residential", {})
        assert result["loan_amount"] > 0

    def test_monthly_payment_positive(self):
        result = calculate_mortgage_financials(500000, "Residential", {})
        assert result["monthly_payment"] > 0


# =============================================================================
# estimate_property_value
# =============================================================================

class TestEstimatePropertyValue:

    def test_returns_float(self):
        result = estimate_property_value({})
        assert isinstance(result, float)

    def test_london_multiplier(self):
        london = estimate_property_value({"county": "Greater London"})
        default = estimate_property_value({})
        # London should generally be higher (not exact due to randomness, but on average)
        assert london > 0

    def test_surrey_multiplier(self):
        result = estimate_property_value({"county": "surrey"})
        assert result > 0

    def test_kent_multiplier(self):
        result = estimate_property_value({"county": "kent"})
        assert result > 0

    def test_with_bedrooms(self):
        result = estimate_property_value({"number_bedrooms": 5})
        assert result > 0

    def test_with_area(self):
        result = estimate_property_value({"property_area_sqm": 120})
        assert result > 0

    def test_new_property(self):
        result = estimate_property_value({"construction_year": 2020})
        assert result > 0

    def test_old_property(self):
        result = estimate_property_value({"construction_year": 1960})
        assert result > 0

    def test_zero_property_value_falls_through(self):
        result = estimate_property_value({"property_value": 0})
        assert result > 0


# =============================================================================
# generate_financial_data
# =============================================================================

class TestGenerateFinancialData:

    def test_returns_dict_with_mortgage_id(self):
        result = generate_financial_data({}, 0)
        assert "mortgage_id" in result
        assert result["mortgage_id"].startswith("MORT-")

    def test_uses_provided_property_value(self):
        result = generate_financial_data({"property_value": 600000}, 0)
        assert result["property_value"] == 600000

    def test_estimates_value_when_zero(self):
        result = generate_financial_data({"property_value": 0}, 0)
        assert result["loan_amount"] > 0

    def test_flood_risk_passed_through(self):
        result = generate_financial_data({"flood_risk": "High"}, 0)
        assert result["flood_risk"] == "High"


# =============================================================================
# _determine_occupancy_type
# =============================================================================

class TestDetermineOccupancyType:

    def test_buy_to_let_returns_investment_or_primary(self):
        result = _determine_occupancy_type("Buy-to-Let")
        assert result in ["Investment", "PrimaryResidence"]

    def test_second_home_returns_second_residence(self):
        assert _determine_occupancy_type("Second Home") == "SecondResidence"

    def test_holiday_home_returns_second_residence(self):
        assert _determine_occupancy_type("Holiday Home") == "SecondResidence"

    def test_residential_returns_primary_or_second(self):
        result = _determine_occupancy_type("Residential")
        assert result in ["PrimaryResidence", "SecondResidence"]
