# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""LoanPricer cashflow/PV pricing engine (price_loan)."""

import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class _PricingMixin:
    """Core single-loan PV pricing (mixed into :class:`LoanPricer`)."""

    def price_loan(self,
                      loan_amount: float,
                      property_value: float,
                      gross_annual_income: float,
                      interest_rate: float,
                      insurance_rate: float,
                      original_maturity: float,
                      current_term: float,
                      recovery_haircut: float,
                      flood_risk_category: Optional[str] = None,
                      discount_rate: Optional[float] = None,
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
            discount_rate: Risk-free rate used to discount expected cashflows.
                When None (default) the contractual ``interest_rate`` is used,
                preserving the legacy flat-discount behaviour. Supplying a
                separate risk-free rate lets the coupon embed a credit/hazard
                margin over the discount curve.
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

        if monthly_rate == 0:  # pragma: no cover - interest_rate clamped to >=0.001 above
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

        # Calculate present values.
        # Discount on the supplied risk-free rate when given; otherwise fall
        # back to the contractual coupon (legacy flat-discount behaviour).
        disc_rate = discount_rate if discount_rate is not None else interest_rate
        disc_rate = max(disc_rate, 0.0)
        periods_array = np.arange(1, n_periods + 1)
        discount_factors = (1 + disc_rate/12) ** (-periods_array)

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
            'discount_rate': disc_rate,
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
