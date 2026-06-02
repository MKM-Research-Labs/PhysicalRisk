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

"""Tests for full pricing pipeline, batch pricing, portfolio metrics, and constructor."""

import pytest

from models.loan.pricer import LoanPricer
from models.loan.portfolio import calculate_portfolio_metrics


class TestPriceMortgage:
    """Tests for the full pricing pipeline."""

    def test_fair_value_less_than_par(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert result["mortgage_value"] < base_loan_params["loan_amount"]
        assert result["discount_to_par"] > 0
        assert result["discount_percentage"] > 0

    def test_survival_monotonically_decreasing(self, pricer, base_loan_params):
        surv = pricer.price_loan(**base_loan_params)["survival_probs"]
        for i in range(1, len(surv)):
            assert surv[i] <= surv[i - 1]

    def test_survival_first_period_less_than_one(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert result["survival_probs"][1] < 1.0

    def test_balance_converges_to_zero(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert result["outstanding_balance"][-1] < 1.0

    def test_hazard_rates_positive(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert result["hazard_rates"][0] == 0.0
        assert all(result["hazard_rates"][i] > 0 for i in range(1, len(result["hazard_rates"])))

    def test_expected_losses_non_negative(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert all(el >= 0 for el in result["expected_losses"])

    def test_ltv_factor_in_result(self, pricer, base_loan_params):
        result = pricer.price_loan(**base_loan_params)
        assert "ltv_factor" in result
        assert result["ltv_factor"] == 1.0  # 400k/500k = 80% LTV

    def test_high_ltv_increases_spread(self, pricer):
        common = dict(
            property_value=500_000, gross_annual_income=75_000, interest_rate=0.035,
            insurance_rate=0.002, original_maturity=25, current_term=20, recovery_haircut=0.25,
        )
        low_ltv = pricer.price_loan(loan_amount=200_000, **common)
        high_ltv = pricer.price_loan(loan_amount=480_000, **common)
        assert high_ltv["credit_spread"] > low_ltv["credit_spread"]
        assert high_ltv["ltv_factor"] > low_ltv["ltv_factor"]

    def test_input_validation_clamps(self, pricer):
        result = pricer.price_loan(
            loan_amount=-100, property_value=-200, gross_annual_income=-50,
            interest_rate=-0.5, insurance_rate=-0.1, original_maturity=-5,
            current_term=-3, recovery_haircut=2.0,
        )
        assert result["mortgage_value"] > 0

    def test_recovery_haircut_zero_low_ltv(self, pricer):
        result = pricer.price_loan(
            loan_amount=200_000, property_value=500_000, gross_annual_income=75_000,
            interest_rate=0.035, insurance_rate=0.002, original_maturity=25,
            current_term=20, recovery_haircut=0.0,
        )
        assert all(lgd == 0 for lgd in result["lgds"])

    def test_higher_haircut_more_loss(self, pricer):
        common = dict(
            loan_amount=400_000, property_value=500_000, gross_annual_income=75_000,
            interest_rate=0.035, insurance_rate=0.002, original_maturity=25,
            current_term=20,
        )
        low = pricer.price_loan(**common, recovery_haircut=0.10)
        high = pricer.price_loan(**common, recovery_haircut=0.50)
        assert high["pv_losses"] > low["pv_losses"]

    def test_raises_on_invalid_types(self, pricer):
        with pytest.raises((TypeError, ValueError)):
            pricer.price_loan(
                loan_amount="invalid", property_value=500_000, gross_annual_income=75_000,
                interest_rate=0.035, insurance_rate=0.002, original_maturity=25,
                current_term=20, recovery_haircut=0.25,
            )


class TestBatchPricing:
    """Tests for batch_price_loans."""

    def test_prices_multiple_mortgages(self, pricer):
        portfolio = [
            {"loan_amount": 200_000, "property_value": 300_000,
             "gross_annual_income": 50_000, "mortgage_id": "M1"},
            {"loan_amount": 400_000, "property_value": 500_000,
             "gross_annual_income": 80_000, "mortgage_id": "M2"},
        ]
        results = pricer.batch_price_loans(portfolio)
        assert len(results) == 2
        assert results[0]["mortgage_id"] == "M1"
        assert results[1]["mortgage_id"] == "M2"

    def test_error_isolation(self, pricer):
        portfolio = [
            {"loan_amount": 200_000, "property_value": 300_000,
             "gross_annual_income": 50_000, "mortgage_id": "GOOD"},
            {"loan_amount": "bad_data", "property_value": 300_000,
             "gross_annual_income": 50_000, "mortgage_id": "BAD"},
            {"loan_amount": 300_000, "property_value": 400_000,
             "gross_annual_income": 60_000, "mortgage_id": "GOOD2"},
        ]
        results = pricer.batch_price_loans(portfolio)
        assert len(results) == 3
        assert "error" not in results[0]
        assert "error" in results[1]
        assert "error" not in results[2]

    def test_default_ids_assigned(self, pricer):
        results = pricer.batch_price_loans(
            [{"loan_amount": 200_000, "property_value": 300_000}]
        )
        assert results[0]["mortgage_id"] == "MORTGAGE_0"
        assert results[0]["property_id"] == "PROPERTY_0"


class TestPortfolioMetrics:
    """Tests for calculate_portfolio_metrics."""

    def test_valid_results(self, pricer):
        portfolio = [
            {"loan_amount": 200_000, "property_value": 300_000, "gross_annual_income": 50_000},
            {"loan_amount": 300_000, "property_value": 400_000, "gross_annual_income": 70_000},
        ]
        results = pricer.batch_price_loans(portfolio)
        metrics = calculate_portfolio_metrics(results)
        assert metrics["total_mortgages"] == 2
        assert metrics["error_count"] == 0
        assert metrics["total_mortgage_value"] > 0
        assert metrics["average_credit_spread"] > 0
        assert metrics["average_ltv"] > 0

    def test_all_errors_returns_error(self):
        results = [
            {"error": "fail1", "mortgage_value": 0},
            {"error": "fail2", "mortgage_value": 0},
        ]
        assert "error" in calculate_portfolio_metrics(results)

    def test_mixed_results_exclude_errors(self, pricer):
        valid = pricer.price_loan(
            loan_amount=200_000, property_value=300_000, gross_annual_income=50_000,
            interest_rate=0.04, insurance_rate=0.002, original_maturity=25,
            current_term=20, recovery_haircut=0.25,
        )
        metrics = calculate_portfolio_metrics([valid, {"error": "pricing failed", "mortgage_value": 0}])
        assert metrics["total_mortgages"] == 1
        assert metrics["error_count"] == 1

    def test_high_risk_count(self):
        results = [
            {"mortgage_value": 100_000, "credit_spread": 0.05,
             "discount_percentage": 5, "ltv_ratio": 0.8, "discount_to_par": 5000},
            {"mortgage_value": 100_000, "credit_spread": 0.15,
             "discount_percentage": 10, "ltv_ratio": 0.95, "discount_to_par": 10000},
        ]
        assert calculate_portfolio_metrics(results)["high_risk_mortgages"] == 1


class TestConstructor:
    """Tests for LoanPricer constructor."""

    def test_default_tax_rate(self):
        assert LoanPricer().tax_rate == 0.20

    def test_custom_tax_rate(self):
        assert LoanPricer(tax_rate=0.40).tax_rate == 0.40

    def test_create_credit_spread_function_delegate(self):
        """Backward-compatible delegate returns a callable interpolation function."""
        fn = LoanPricer()._create_credit_spread_function()
        assert callable(fn)
        # interpolation function should return a finite spread for a mid ratio
        assert float(fn(0.5)) >= 0.0


class TestDebugAndEdgeCases:
    """Tests for debug branch and zero-rate branch coverage."""

    def _base(self):
        return dict(
            loan_amount=400_000,
            property_value=500_000,
            gross_annual_income=75_000,
            interest_rate=0.035,
            insurance_rate=0.002,
            original_maturity=25,
            current_term=20,
            recovery_haircut=0.25,
        )

    def test_debug_true_does_not_crash(self):
        """debug=True exercises logging branches without error."""
        pricer = LoanPricer()
        result = pricer.price_loan(**self._base(), debug=True)
        assert result["mortgage_value"] > 0

    def test_debug_also_in_credit_spread(self):
        """debug=True in the credit spread calculation."""
        pricer = LoanPricer()
        result = pricer.price_loan(**self._base(), flood_risk_category="High", debug=True)
        assert "credit_spread" in result

    def test_zero_interest_rate(self):
        """When interest_rate=0, monthly_rate==0 → loan_amount/n_periods formula."""
        pricer = LoanPricer()
        result = pricer.price_loan(**{**self._base(), "interest_rate": 0.0})
        assert result["mortgage_value"] > 0

    def test_debug_with_zero_income(self):
        """Zero income with debug=True exercises zero-income debug branch."""
        pricer = LoanPricer()
        result = pricer.price_loan(
            **{**self._base(), "gross_annual_income": 0.0, "debug": True}
        )
        assert result["credit_spread"] > 0

    def test_flood_risk_none_with_debug(self):
        """flood_risk_category=None with debug=True."""
        pricer = LoanPricer()
        result = pricer.price_loan(**self._base(), flood_risk_category=None, debug=True)
        assert result["mortgage_value"] > 0
