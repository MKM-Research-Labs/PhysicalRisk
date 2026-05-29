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

"""Tests for credit spread, LTV risk factor, and flood risk factor."""

import pytest

from models.loan.pricer import LoanPricer


class TestCreditSpread:
    """Tests for calculate_credit_spread."""

    def test_floor_at_10bps(self, pricer):
        spread = pricer.calculate_credit_spread(
            gross_annual_income=500_000, annual_payment=5_000,
            insurance_rate=0.001, property_value=500_000,
            original_maturity=25, current_term=12,
        )
        assert spread >= 0.001

    def test_zero_income_fallback(self, pricer):
        spread = pricer.calculate_credit_spread(
            gross_annual_income=0, annual_payment=12_000,
            insurance_rate=0.002, property_value=300_000,
            original_maturity=25, current_term=20,
        )
        assert spread == 0.15

    def test_negative_income_fallback(self, pricer):
        spread = pricer.calculate_credit_spread(
            gross_annual_income=-10_000, annual_payment=12_000,
            insurance_rate=0.002, property_value=300_000,
            original_maturity=25, current_term=20,
        )
        assert spread == 0.15

    def test_higher_affordability_higher_spread(self, pricer):
        spread_high_income = pricer.calculate_credit_spread(
            gross_annual_income=100_000, annual_payment=12_000,
            insurance_rate=0.002, property_value=300_000,
            original_maturity=25, current_term=20,
        )
        spread_low_income = pricer.calculate_credit_spread(
            gross_annual_income=30_000, annual_payment=12_000,
            insurance_rate=0.002, property_value=300_000,
            original_maturity=25, current_term=20,
        )
        assert spread_low_income > spread_high_income

    def test_custom_tax_rate(self, pricer):
        spread_low_tax = pricer.calculate_credit_spread(
            gross_annual_income=50_000, annual_payment=15_000,
            insurance_rate=0.002, property_value=300_000,
            original_maturity=25, current_term=20, tax_rate=0.10,
        )
        spread_high_tax = pricer.calculate_credit_spread(
            gross_annual_income=50_000, annual_payment=15_000,
            insurance_rate=0.002, property_value=300_000,
            original_maturity=25, current_term=20, tax_rate=0.40,
        )
        assert spread_high_tax > spread_low_tax

    def test_spread_bounded_by_schedule(self, pricer):
        spread = pricer.calculate_credit_spread(
            gross_annual_income=1_000_000, annual_payment=1_000,
            insurance_rate=0.0, property_value=100_000,
            original_maturity=25, current_term=12,
        )
        assert spread >= 0.001
        assert spread < 0.05


class TestLTVRiskFactor:
    """Tests for calculate_loan_to_value_impact."""

    @pytest.mark.parametrize("ltv,expected", [
        (0.50, 1.0),
        (0.80, 1.0),
        (0.85, 1.1),
        (0.90, 1.1),
        (0.91, 1.3),
        (0.95, 1.3),
        (0.96, 1.5),
        (1.00, 1.5),
    ])
    def test_ltv_thresholds(self, pricer, ltv, expected):
        pv = 500_000
        assert pricer.calculate_loan_to_value_impact(pv * ltv, pv) == expected

    def test_zero_property_value(self, pricer):
        assert pricer.calculate_loan_to_value_impact(100_000, 0) == 1.5


class TestFloodRiskFactor:
    """Tests for calculate_flood_risk_impact."""

    @pytest.mark.parametrize("category,expected", [
        ("Very Low", 1.00),
        ("Low", 1.05),
        ("Medium", 1.20),
        ("High", 1.40),
        ("Very High", 1.75),
    ])
    def test_flood_risk_multipliers(self, category, expected):
        assert LoanPricer.calculate_flood_risk_impact(category) == expected

    def test_none_returns_unity(self):
        assert LoanPricer.calculate_flood_risk_impact(None) == 1.0

    def test_unknown_category_returns_unity(self):
        assert LoanPricer.calculate_flood_risk_impact("Unknown") == 1.0
        assert LoanPricer.calculate_flood_risk_impact("Extreme") == 1.0

    def test_case_insensitive(self):
        assert LoanPricer.calculate_flood_risk_impact("very high") == 1.75
        assert LoanPricer.calculate_flood_risk_impact("VERY LOW") == 1.00
        assert LoanPricer.calculate_flood_risk_impact("medium") == 1.20

    def test_flood_risk_increases_spread(self, pricer):
        base = dict(
            loan_amount=400_000, property_value=500_000,
            gross_annual_income=75_000, interest_rate=0.035,
            insurance_rate=0.002, original_maturity=25,
            current_term=20, recovery_haircut=0.25,
        )
        low = pricer.price_loan(**base, flood_risk_category="Very Low")
        high = pricer.price_loan(**base, flood_risk_category="Very High")
        assert high["credit_spread"] > low["credit_spread"]
        assert high["flood_risk_factor"] > low["flood_risk_factor"]
        assert high["mortgage_value"] < low["mortgage_value"]

    def test_flood_factor_in_result(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params, flood_risk_category="Medium")
        assert result["flood_risk_factor"] == 1.20

    def test_no_flood_risk_defaults_to_unity(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert result["flood_risk_factor"] == 1.0

    def test_batch_passes_flood_risk(self, pricer):
        portfolio = [
            {"loan_amount": 200_000, "property_value": 300_000,
             "gross_annual_income": 50_000, "flood_risk_category": "High"},
            {"loan_amount": 200_000, "property_value": 300_000,
             "gross_annual_income": 50_000, "flood_risk_category": "Very Low"},
        ]
        results = pricer.batch_price_loans(portfolio)
        assert results[0]["flood_risk_factor"] == 1.40
        assert results[1]["flood_risk_factor"] == 1.00
        assert results[0]["credit_spread"] > results[1]["credit_spread"]
