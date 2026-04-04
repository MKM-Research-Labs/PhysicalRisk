# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""MortgagePricer — main pricing engine with cashflow modelling."""

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

logger = logging.getLogger(__name__)


class MortgagePricer:
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
        monthly_payment = MortgagePricer.calculate_monthly_payment(
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

    def price_mortgage(self,
                      loan_amount: float,
                      property_value: float,
                      gross_annual_income: float,
                      interest_rate: float,
                      insurance_rate: float,
                      original_maturity: float,
                      current_term: float,
                      recovery_haircut: float,
                      flood_risk_category: Optional[str] = None,
                      tax_rate: Optional[float] = None,
                      debug: bool = False) -> Dict[str, Any]:
        """
        Price a mortgage considering credit risk and expected losses.

        Args:
            loan_amount: Outstanding mortgage amount
            property_value: Current property value
            gross_annual_income: Borrower's gross annual income
            interest_rate: Base interest rate (as decimal)
            insurance_rate: Insurance rate (as decimal of property value)
            original_maturity: Original mortgage term in years
            current_term: Remaining term in years
            recovery_haircut: Recovery haircut in default (as decimal)
            flood_risk_category: Flood risk category ("Very Low" to "Very High")
            tax_rate: Tax rate (optional)
            debug: Whether to print detailed calculations

        Returns:
            Dictionary containing pricing results and intermediate calculations
        """
        # Input validation and normalization
        loan_amount = max(loan_amount, 1)
        property_value = max(property_value, 1)
        gross_annual_income = max(gross_annual_income, 1)
        interest_rate = max(interest_rate, 0.001)  # Minimum 0.1%
        insurance_rate = max(insurance_rate, 0)
        original_maturity = max(original_maturity, 1)
        current_term = max(min(current_term, original_maturity), 0.5)
        recovery_haircut = max(min(recovery_haircut, 0.95), 0)  # Cap at 95%

        effective_tax_rate = tax_rate if tax_rate is not None else self.tax_rate

        # Calculate payment schedule
        n_periods = int(current_term * 12)
        monthly_rate = interest_rate / 12

        if monthly_rate == 0:
            monthly_payment = loan_amount / n_periods
        else:
            monthly_payment = loan_amount * monthly_rate / (1 - (1 + monthly_rate)**(-n_periods))

        annual_payment = monthly_payment * 12

        if debug:
            logger.debug("Mortgage Pricing Inputs:")
            logger.debug("  Loan Amount: £%s", f"{loan_amount:,.2f}")
            logger.debug("  Property Value: £%s", f"{property_value:,.2f}")
            logger.debug("  Interest Rate: %.2f%%", interest_rate*100)
            logger.debug("  Current Term: %.1f years", current_term)
            logger.debug("  Monthly Payment: £%s", f"{monthly_payment:,.2f}")
            logger.debug("  Annual Payment: £%s", f"{annual_payment:,.2f}")

        # Calculate credit spread
        credit_spread = self.calculate_credit_spread(
            gross_annual_income, annual_payment, insurance_rate,
            property_value, original_maturity, current_term,
            effective_tax_rate, debug
        )

        # Apply LTV risk adjustment to credit spread
        ltv_factor = self.calculate_loan_to_value_impact(loan_amount, property_value)
        credit_spread *= ltv_factor

        # Apply flood risk adjustment to credit spread
        flood_factor = self.calculate_flood_risk_impact(flood_risk_category)
        credit_spread *= flood_factor

        if debug:
            logger.debug("  LTV Factor: %.2f", ltv_factor)
            logger.debug("  Flood Risk Factor: %.2f (%s)", flood_factor,
                         flood_risk_category or 'None')
            logger.debug("  Adjusted Credit Spread: %.4f", credit_spread)

        # Initialize time series arrays
        outstanding_balance = np.zeros(n_periods + 1)
        outstanding_balance[0] = loan_amount

        credit_spreads = np.full(n_periods + 1, credit_spread)
        hazard_rates = np.zeros(n_periods + 1)
        survival_probs = np.zeros(n_periods + 1)
        survival_probs[0] = 1.0
        lgds = np.zeros(n_periods + 1)  # Loss Given Default

        # Calculate time series for each period
        for i in range(1, n_periods + 1):
            # Update outstanding balance
            interest_payment = outstanding_balance[i-1] * monthly_rate
            principal_payment = monthly_payment - interest_payment
            outstanding_balance[i] = max(0, outstanding_balance[i-1] - principal_payment)

            # Calculate Loss Given Default
            # Note: recovery value uses static property_value (no price dynamics modelled)
            recovery_value = (1 - recovery_haircut) * property_value
            lgds[i] = max(0, outstanding_balance[i] - recovery_value)

            # Calculate hazard rate (probability of default this period)
            hazard_rates[i] = 1 - np.exp(-credit_spreads[i] / 12)

            # Survival probability: S_i = S_{i-1} * (1 - h_i)
            survival_probs[i] = survival_probs[i-1] * (1 - hazard_rates[i])

        # Calculate expected cashflows and losses
        expected_cashflows = np.zeros(n_periods)
        expected_losses = np.zeros(n_periods)

        for i in range(n_periods):
            period_idx = i + 1

            # Probability of default in this period
            default_prob = max(0, survival_probs[i] - survival_probs[period_idx])

            # Expected cashflow: payment if survives + recovery if defaults
            expected_cashflows[i] = (monthly_payment * survival_probs[period_idx] +
                                   (outstanding_balance[i] - lgds[period_idx]) * default_prob)

            # Expected loss in this period
            expected_losses[i] = lgds[period_idx] * default_prob

        # Calculate present values
        periods_array = np.arange(1, n_periods + 1)
        discount_factors = (1 + interest_rate/12) ** (-periods_array)

        pv_cashflows = np.sum(expected_cashflows * discount_factors)
        pv_losses = np.sum(expected_losses * discount_factors)
        mortgage_value = pv_cashflows - pv_losses

        if debug:
            logger.debug("Pricing Results:")
            logger.debug("  Credit Spread: %.3f%%", credit_spread*100)
            logger.debug("  PV Expected Cashflows: £%s", f"{pv_cashflows:,.2f}")
            logger.debug("  PV Expected Losses: £%s", f"{pv_losses:,.2f}")
            logger.debug("  Mortgage Fair Value: £%s", f"{mortgage_value:,.2f}")
            logger.debug("  Discount to Par: £%s", f"{loan_amount - mortgage_value:,.2f}")
            logger.debug("  Discount Percentage: %.2f%%", ((loan_amount - mortgage_value)/loan_amount)*100)

        # Compile comprehensive results
        return {
            'mortgage_value': mortgage_value,
            'credit_spread': credit_spread,
            'ltv_factor': ltv_factor,
            'flood_risk_factor': flood_factor,
            'annual_payment': annual_payment,
            'monthly_payment': monthly_payment,
            'outstanding_balance': outstanding_balance,
            'hazard_rates': hazard_rates,
            'lgds': lgds,
            'survival_probs': survival_probs,
            'expected_cashflows': expected_cashflows,
            'expected_losses': expected_losses,
            'pv_cashflows': pv_cashflows,
            'pv_losses': pv_losses,
            'discount_to_par': loan_amount - mortgage_value,
            'discount_percentage': ((loan_amount - mortgage_value)/loan_amount)*100,
            'ltv_ratio': loan_amount / property_value,
            'affordability_ratio': (annual_payment + insurance_rate * property_value) /
                                 (gross_annual_income * (1 - effective_tax_rate))
        }

    def batch_price_mortgages(self, mortgage_portfolio: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                pricing_result = self.price_mortgage(
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
