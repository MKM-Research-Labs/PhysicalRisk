# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Quality and consistency checks for generated mortgage data."""

from typing import Dict


def quality_consistency_check(mortgage_data: Dict, financial_data: Dict) -> Dict:
    """Perform quality and consistency checks on generated mortgage data."""
    mortgage = mortgage_data.get('Mortgage', {})
    loan = mortgage.get('LoanDetails', {})

    original = loan.get('OriginalLoanAmount', 400000)
    current = loan.get('CurrentBalance', 380000)
    if current > original:
        loan['CurrentBalance'] = original * 0.95

    ltv = loan.get('LTV', 80)
    if ltv > 100:
        loan['LTV'] = 95
    elif ltv < 10:
        loan['LTV'] = 60

    interest_rate = loan.get('InterestRate', 4.5)
    if interest_rate > 15:
        loan['InterestRate'] = 12.0
    elif interest_rate < 1:
        loan['InterestRate'] = 2.0

    return mortgage_data
