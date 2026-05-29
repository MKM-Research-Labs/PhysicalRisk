# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Property popup helpers — pure calculation functions for LTV, term, and monthly payment."""

from typing import Any, Dict, Optional


def calculate_ltv_ratio(loan_amount: Any, property_value: Any,
                        mortgage_financial: Dict[str, Any]) -> float:
    """Calculate LTV ratio from available data."""
    if (isinstance(loan_amount, (int, float)) and property_value and
            isinstance(property_value, (int, float)) and property_value > 0):
        return loan_amount / property_value
    else:
        return mortgage_financial.get('LoanToValueRatio', 0)


def extract_term_years(mortgage_financial: Dict[str, Any],
                       rloan_info: Dict[str, Any]) -> Optional[float]:
    """Extract term years from various possible fields."""
    for field in ['TermYears', 'Term', 'LoanTerm', 'OriginalTerm']:
        if field in mortgage_financial:
            term_years = mortgage_financial.get(field)
            if field == 'OriginalTerm' and term_years and term_years > 100:
                return term_years / 12
            return term_years

    for path in [
        ['term_years'],
        ['Term', 'Years'],
        ['LoanTerms', 'Years']
    ]:
        current = rloan_info
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                current = None
                break
        if current is not None:
            return current

    return None


def calculate_monthly_payment(mortgage_financial: Dict[str, Any],
                              loan_amount: Any, interest_rate: Any,
                              term_years: Any) -> Optional[float]:
    """Calculate monthly payment from loan terms."""
    for field in ['MonthlyPayment', 'Payment', 'RegularPayment']:
        if field in mortgage_financial:
            return mortgage_financial.get(field)

    if (isinstance(loan_amount, (int, float)) and
            isinstance(interest_rate, (int, float)) and
            isinstance(term_years, (int, float))):

        monthly_rate = interest_rate / 100 / 12
        num_payments = term_years * 12

        if monthly_rate > 0 and num_payments > 0:
            try:
                return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            except Exception:
                pass

    return None
