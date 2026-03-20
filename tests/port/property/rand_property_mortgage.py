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
Unit tests for Thames property and mortgage random value generators.
"""

import re

import pytest

# =============================================================================
# Property random generators
# =============================================================================

@pytest.mark.random_values
class TestCalculatePropertyValuation:
    """Direct tests for property_valuation.py functions."""

    def _loc(self, **kwargs):
        base = {
            "property_type": "Semi-detached",
            "value_factor": 1.0,
            "property_area": 100.0,
            "construction_year": 1990,
            "property_condition": "Good",
            "flood_risk": "Low",
            "epc_rating": "C",
            "distance_to_thames": 500,
        }
        base.update(kwargs)
        return base

    def test_calculate_sale_price_positive(self):
        from port.rand.thames.property.property_valuation import calculate_sale_price
        info = self._loc(property_value=500_000)
        price = calculate_sale_price(info)
        assert isinstance(price, float)
        assert 50_000 <= price <= 8_000_000

    def test_calculate_sale_price_no_current_value(self):
        """Lines 120-121: property_value=None → computes it first."""
        from port.rand.thames.property.property_valuation import calculate_sale_price
        info = self._loc()  # no property_value key
        price = calculate_sale_price(info)
        assert isinstance(price, float)
        assert price > 0

    def test_calculate_sale_price_with_sale_date_recent(self):
        """Lines 124-128: sale_date within 1 year."""
        from port.rand.thames.property.property_valuation import calculate_sale_price
        info = self._loc(property_value=500_000, sale_date="2025-06-01")
        price = calculate_sale_price(info)
        assert isinstance(price, float)

    def test_calculate_sale_price_with_sale_date_1_to_2_years(self):
        """Lines 135-137: sale_date 1-2 years ago."""
        from port.rand.thames.property.property_valuation import calculate_sale_price
        info = self._loc(property_value=500_000, sale_date="2024-06-01")
        price = calculate_sale_price(info)
        assert isinstance(price, float)

    def test_calculate_sale_price_with_sale_date_over_2_years(self):
        """Lines 139-140: sale_date > 2 years ago."""
        from port.rand.thames.property.property_valuation import calculate_sale_price
        info = self._loc(property_value=500_000, sale_date="2020-01-01")
        price = calculate_sale_price(info)
        assert isinstance(price, float)

    def test_calculate_sale_price_invalid_date_falls_back(self):
        """Lines 128-129: invalid date format → random years_ago."""
        from port.rand.thames.property.property_valuation import calculate_sale_price
        info = self._loc(property_value=500_000, sale_date="not-a-date")
        price = calculate_sale_price(info)
        assert isinstance(price, float)

    def test_calculate_monthly_rent_positive(self):
        from port.rand.thames.property.property_valuation import calculate_monthly_rent
        info = self._loc(property_value=500_000, property_area=100.0)
        rent = calculate_monthly_rent(info)
        assert isinstance(rent, float)
        assert 800 <= rent <= 15_000

    def test_calculate_monthly_rent_no_value(self):
        """Lines 162-163: property_value=None → computes it first."""
        from port.rand.thames.property.property_valuation import calculate_monthly_rent
        info = self._loc(property_area=100.0)
        rent = calculate_monthly_rent(info)
        assert isinstance(rent, float)
        assert rent > 0

    def test_calculate_monthly_rent_no_area(self):
        """Lines 165-166: area=None → computes it first."""
        from port.rand.thames.property.property_valuation import calculate_monthly_rent
        info = self._loc(property_value=500_000)
        rent = calculate_monthly_rent(info)
        assert isinstance(rent, float)
        assert rent > 0

    def test_calculate_monthly_rent_all_types(self):
        from port.rand.thames.property.property_valuation import calculate_monthly_rent
        for ptype in ["Flat", "Terraced", "Semi-detached", "Detached"]:
            info = self._loc(property_value=400_000, property_area=80.0, property_type=ptype)
            rent = calculate_monthly_rent(info)
            assert 800 <= rent <= 15_000

    def test_calculate_insurance_premium_no_value(self):
        """Line 211: property_value=None → computes it first."""
        from port.rand.thames.property.property_valuation import calculate_insurance_premium
        info = self._loc(property_area=100.0)
        premium = calculate_insurance_premium(info)
        assert isinstance(premium, float)
        assert premium > 0

    def test_calculate_insurance_premium_no_area(self):
        """Line 214: area=None → computes it first."""
        from port.rand.thames.property.property_valuation import calculate_insurance_premium
        info = self._loc(property_value=500_000)
        premium = calculate_insurance_premium(info)
        assert isinstance(premium, float)
        assert premium > 0

    def test_calculate_insurance_premium_flood_risk_high(self):
        from port.rand.thames.property.property_valuation import calculate_insurance_premium
        info = self._loc(property_value=400_000, property_area=80.0, flood_risk="Very High")
        premium = calculate_insurance_premium(info)
        assert premium > 0

    def test_calculate_property_area_all_types(self):
        from port.rand.thames.property.property_valuation import calculate_property_area
        for ptype in ["Flat", "Terraced", "Semi-detached", "Detached", "Unknown"]:
            area = calculate_property_area({"property_type": ptype})
            assert area > 0


@pytest.mark.random_values
class TestPropertyMetadata:

    def test_returns_dict_with_required_keys(self, thames_property_random, sample_property_location):
        meta = thames_property_random.generate_property_metadata(0, sample_property_location)
        assert "property_id" in meta
        assert "property_type" in meta

    def test_property_id_format(self, thames_property_random, sample_property_location):
        meta = thames_property_random.generate_property_metadata(0, sample_property_location)
        assert re.match(r"^PROP-[a-f0-9]{8}$", meta["property_id"])

    def test_construction_year_in_range(self, thames_property_random):
        for _ in range(20):
            year = thames_property_random.generate_construction_year()
            assert 1600 <= year <= 2026


@pytest.mark.random_values
class TestPropertyCalculations:

    def test_calculate_property_value_in_range(self, thames_property_random, sample_property_location):
        for _ in range(10):
            value = thames_property_random.calculate_property_value(sample_property_location)
            assert 50_000 <= value <= 10_000_000

    def test_generate_postcode_format(self, thames_property_random):
        for _ in range(10):
            postcode = thames_property_random.generate_postcode()
            assert isinstance(postcode, str)
            assert len(postcode) >= 5

    def test_generate_bedrooms_flat(self, thames_property_random):
        info = {"property_type": "Flat"}
        for _ in range(20):
            beds = thames_property_random.generate_bedrooms(info)
            assert isinstance(beds, int)
            assert 1 <= beds <= 4

    def test_generate_bedrooms_detached(self, thames_property_random):
        info = {"property_type": "Detached"}
        for _ in range(20):
            beds = thames_property_random.generate_bedrooms(info)
            assert isinstance(beds, int)
            assert 1 <= beds <= 7

    def test_calculate_insurance_premium_positive(self, thames_property_random, sample_property_location):
        info = {**sample_property_location, "property_value": 500000}
        premium = thames_property_random.calculate_insurance_premium(info)
        assert isinstance(premium, (int, float))
        assert premium > 0

    def test_calculate_property_area_positive(self, thames_property_random, sample_property_location):
        area = thames_property_random.calculate_property_area(sample_property_location)
        assert isinstance(area, (int, float))
        assert area > 0


@pytest.mark.random_values
class TestPropertyFieldValue:

    def test_generate_field_value_text(self, thames_property_random, sample_property_location):
        meta = thames_property_random.generate_property_metadata(0, sample_property_location)
        val = thames_property_random.generate_field_value(
            "PropertyID", {"type": "text"}, 0, meta
        )
        assert isinstance(val, str)

    def test_generate_field_value_decimal(self, thames_property_random, sample_property_location):
        meta = thames_property_random.generate_property_metadata(0, sample_property_location)
        val = thames_property_random.generate_field_value(
            "PropertyValue", {"type": "decimal"}, 0, meta
        )
        assert isinstance(val, (int, float))


# =============================================================================
# Mortgage random generators
# =============================================================================

@pytest.mark.random_values
class TestMortgageFinancials:

    def _make_property_info(self):
        return {
            "property_id": "PROP-test1234",
            "property_type": "Semi-detached",
            "property_value": 500000,
            "lat": 51.5,
            "lon": -0.1,
        }

    def test_generate_financial_data_keys(self, thames_mortgage_random):
        info = self._make_property_info()
        data = thames_mortgage_random.generate_financial_data(info, 0)
        assert "mortgage_id" in data
        assert "loan_amount" in data
        assert "interest_rate" in data

    def test_mortgage_id_format(self, thames_mortgage_random):
        info = self._make_property_info()
        data = thames_mortgage_random.generate_financial_data(info, 0)
        assert re.match(r"^MORT-[a-f0-9]{8}$", data["mortgage_id"])

    def test_loan_amount_less_than_value(self, thames_mortgage_random):
        info = self._make_property_info()
        for _ in range(10):
            data = thames_mortgage_random.generate_financial_data(info, 0)
            assert data["loan_amount"] <= info["property_value"] * 1.05

    def test_interest_rate_range(self, thames_mortgage_random):
        info = self._make_property_info()
        for _ in range(10):
            data = thames_mortgage_random.generate_financial_data(info, 0)
            assert 0.01 <= data["interest_rate"] <= 0.15

    def test_calculate_mortgage_financials_returns_dict(self, thames_mortgage_random):
        result = thames_mortgage_random.calculate_mortgage_financials(
            500000, "Residential", {}, index=0
        )
        assert isinstance(result, dict)
        assert "loan_amount" in result
        assert "monthly_payment" in result
        assert result["monthly_payment"] > 0

    def test_quality_consistency_check(self, thames_mortgage_random):
        mortgage_data = {
            "Mortgage": {
                "CurrentStatus": {
                    "OutstandingBalance": 600000,  # > original
                    "CurrentLTV": 120,  # > 100
                },
                "FinancialTerms": {
                    "OriginalLoan": 400000,
                },
            }
        }
        financial_data = {"loan_amount": 400000, "property_value": 500000}
        corrected = thames_mortgage_random.quality_consistency_check(
            mortgage_data, financial_data
        )
        assert isinstance(corrected, dict)
