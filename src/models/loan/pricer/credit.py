# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Credit spread calculation — affordability, LTV, flood risk multipliers."""

import logging
from typing import Optional

from scipy import interpolate

from config.models import FLOOD_RISK_MULTIPLIERS

logger = logging.getLogger(__name__)


def create_credit_spread_function():
    """
    Create interpolation function for credit spreads based on affordability ratios.

    Returns:
        Function that interpolates credit spreads based on affordability
    """
    # Affordability ratio points (total cost / after-tax income)
    affordability_ratios = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    # Corresponding credit spreads (annual)
    credit_spreads = [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35]

    return interpolate.interp1d(
        affordability_ratios, credit_spreads,
        kind='linear', bounds_error=False,
        fill_value=(credit_spreads[0], credit_spreads[-1])
    )


def calculate_flood_risk_impact(flood_risk_category: Optional[str] = None) -> float:
    """
    Calculate flood-risk-based credit spread multiplier.

    Multipliers are calibrated to RiskAssessor value-at-risk percentages
    (1%, 5%, 15%, 35%, 60%) scaled into spread adjustment factors.

    Args:
        flood_risk_category: One of "Very Low", "Low", "Medium", "High",
                             "Very High" (case-insensitive), or None

    Returns:
        Risk adjustment factor (1.0 = no adjustment, >1.0 = higher risk)
    """
    if flood_risk_category is None:
        return 1.0
    normalised = flood_risk_category.strip().title()
    return FLOOD_RISK_MULTIPLIERS.get(normalised, 1.0)


def calculate_loan_to_value_impact(loan_amount: float, property_value: float) -> float:
    """
    Calculate LTV-based risk adjustment factor.

    Args:
        loan_amount: Outstanding loan amount
        property_value: Current property value

    Returns:
        Risk adjustment factor (1.0 = no adjustment, >1.0 = higher risk)
    """
    ltv = loan_amount / property_value if property_value > 0 else 1.0

    # LTV-based risk adjustments
    if ltv > 0.95:
        return 1.5      # Very high LTV
    elif ltv > 0.9:
        return 1.3      # High LTV
    elif ltv > 0.8:
        return 1.1      # Moderate LTV
    else:
        return 1.0      # Standard LTV


def calculate_credit_spread(
    credit_spread_function,
    gross_annual_income: float,
    annual_payment: float,
    insurance_rate: float,
    property_value: float,
    original_maturity: float,
    current_term: float,
    tax_rate: float,
    debug: bool = False,
) -> float:
    """
    Calculate credit spread based on borrower affordability and loan characteristics.

    Args:
        credit_spread_function: Interpolation function for base spreads
        gross_annual_income: Borrower's gross annual income
        annual_payment: Annual mortgage payment
        insurance_rate: Insurance rate (as decimal of property value)
        property_value: Current property value
        original_maturity: Original loan term in years
        current_term: Remaining loan term in years
        tax_rate: Tax rate
        debug: Whether to print debug information

    Returns:
        Credit spread as decimal (e.g., 0.05 = 5%)
    """
    # Handle edge case of zero income
    if gross_annual_income <= 0:
        if debug:
            logger.debug("Zero/negative income, using default high spread")
        return 0.15  # 15% default spread for missing income data

    # Calculate affordability metrics
    after_tax_income = gross_annual_income * (1 - tax_rate)
    annual_insurance_cost = insurance_rate * property_value
    total_annual_cost = annual_payment + annual_insurance_cost
    affordability_ratio = total_annual_cost / after_tax_income

    # Cap affordability ratio to reasonable bounds
    affordability_ratio = max(0.1, min(affordability_ratio, 1.0))

    # Calculate base credit spread
    base_spread = float(credit_spread_function(affordability_ratio))

    # Apply term structure adjustment
    original_maturity = max(original_maturity, 1)  # Minimum 1 year
    current_term = max(current_term, 0.5)          # Minimum 6 months

    # Term factor: longer remaining terms get slightly higher spreads
    term_factor = 1 + (current_term - original_maturity / 2) / 100
    credit_spread = base_spread * term_factor

    if debug:
        logger.debug("Credit Spread Calculation:")
        logger.debug("  Gross Income: £%s", f"{gross_annual_income:,.2f}")
        logger.debug("  After-tax Income: £%s", f"{after_tax_income:,.2f}")
        logger.debug("  Annual Payment: £%s", f"{annual_payment:,.2f}")
        logger.debug("  Annual Insurance: £%s", f"{annual_insurance_cost:,.2f}")
        logger.debug("  Total Annual Cost: £%s", f"{total_annual_cost:,.2f}")
        logger.debug("  Affordability Ratio: %.3f", affordability_ratio)
        logger.debug("  Base Spread: %.4f", base_spread)
        logger.debug("  Term Factor: %.4f", term_factor)
        logger.debug("  Final Credit Spread: %.4f", credit_spread)

    return max(0.001, credit_spread)  # Minimum 0.1% spread
