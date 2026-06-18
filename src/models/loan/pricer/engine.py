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

"""LoanPricer — main pricing engine with cashflow modelling."""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from config.models import FLOOD_RISK_MULTIPLIERS
from .credit import (
    calculate_credit_spread,
    calculate_flood_risk_impact,
    calculate_loan_to_value_impact,
    create_credit_spread_function,
)
from ._pricing import _PricingMixin

logger = logging.getLogger(__name__)


class LoanPricer(_PricingMixin):
    """
    Mortgage pricing engine that calculates present value of mortgages considering
    credit risk, affordability, and external risk factors like flood risk.
    """

    # Expose at class level for backward compatibility
    FLOOD_RISK_MULTIPLIERS = FLOOD_RISK_MULTIPLIERS

    def __init__(self, tax_rate: float = 0.20):
        """
        Initialize the mortgage pricer.

        Args:
            tax_rate: Income tax rate used for affordability calculation (default 20%)
        """
        self.tax_rate = tax_rate
        self.credit_spread_function = create_credit_spread_function()

    def _create_credit_spread_function(self):
        """Backward-compatible delegate."""
        return create_credit_spread_function()

    @staticmethod
    def calculate_monthly_payment(principal: float, annual_interest_rate: float,
                                  term_years: int) -> float:
        """
        Calculate standard monthly mortgage payment.

        Args:
            principal: Loan principal amount
            annual_interest_rate: Annual interest rate (as decimal, e.g. 0.035)
            term_years: Loan term in years

        Returns:
            Monthly payment amount
        """
        monthly_rate = annual_interest_rate / 12
        num_payments = term_years * 12

        if monthly_rate == 0:
            return principal / num_payments

        payment = (principal * monthly_rate * (1 + monthly_rate)**num_payments) / \
                  ((1 + monthly_rate)**num_payments - 1)

        return payment

    @staticmethod
    def calculate_total_cost(principal: float, annual_interest_rate: float,
                             term_years: int) -> float:
        """
        Calculate total cost of the mortgage over its lifetime.

        Args:
            principal: Loan principal amount
            annual_interest_rate: Annual interest rate (as decimal, e.g. 0.035)
            term_years: Loan term in years

        Returns:
            Total amount paid over the loan term
        """
        monthly_payment = LoanPricer.calculate_monthly_payment(
            principal, annual_interest_rate, term_years
        )
        return monthly_payment * term_years * 12

    def calculate_credit_spread(self,
                              gross_annual_income: float,
                              annual_payment: float,
                              insurance_rate: float,
                              property_value: float,
                              original_maturity: float,
                              current_term: float,
                              tax_rate: Optional[float] = None,
                              debug: bool = False) -> float:
        """
        Calculate credit spread based on borrower affordability and loan characteristics.

        Delegates to :func:`credit.calculate_credit_spread`.
        """
        effective_tax_rate = tax_rate if tax_rate is not None else self.tax_rate
        return calculate_credit_spread(
            self.credit_spread_function,
            gross_annual_income, annual_payment, insurance_rate,
            property_value, original_maturity, current_term,
            effective_tax_rate, debug,
        )

    @staticmethod
    def calculate_flood_risk_impact(flood_risk_category: Optional[str] = None) -> float:
        """Calculate flood-risk-based credit spread multiplier."""
        return calculate_flood_risk_impact(flood_risk_category)

    def calculate_loan_to_value_impact(self, loan_amount: float, property_value: float) -> float:
        """Calculate LTV-based risk adjustment factor."""
        return calculate_loan_to_value_impact(loan_amount, property_value)
    def batch_price_loans(self, mortgage_portfolio: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Price a batch of mortgages efficiently.

        Args:
            mortgage_portfolio: List of mortgage dictionaries with required fields

        Returns:
            List of pricing results for each mortgage
        """
        results = []

        for i, mortgage in enumerate(mortgage_portfolio):
            try:
                pricing_result = self.price_loan(
                    loan_amount=mortgage.get('loan_amount', 0),
                    property_value=mortgage.get('property_value', 0),
                    gross_annual_income=mortgage.get('gross_annual_income', 50000),
                    interest_rate=mortgage.get('interest_rate', 0.035),
                    insurance_rate=mortgage.get('insurance_rate', 0.002),
                    original_maturity=mortgage.get('original_maturity', 30),
                    current_term=mortgage.get('current_term', 30),
                    recovery_haircut=mortgage.get('recovery_haircut', 0.2),
                    flood_risk_category=mortgage.get('flood_risk_category'),
                )

                pricing_result['mortgage_id'] = mortgage.get('mortgage_id', f'MORTGAGE_{i}')
                pricing_result['property_id'] = mortgage.get('property_id', f'PROPERTY_{i}')

                results.append(pricing_result)

            except Exception as e:
                results.append({
                    'mortgage_id': mortgage.get('mortgage_id', f'MORTGAGE_{i}'),
                    'property_id': mortgage.get('property_id', f'PROPERTY_{i}'),
                    'error': str(e),
                    'mortgage_value': 0
                })

        return results
