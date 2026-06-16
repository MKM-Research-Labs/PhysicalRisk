# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Quality and consistency checks for generated mortgage data."""

from typing import Dict


def quality_consistency_check(mortgage_data: Dict, financial_data: Dict) -> Dict:
    """Perform quality and consistency checks on generated mortgage data.

    Clamps the canonical CDM fields (FinancialTerms / CurrentStatus) so the
    constraints apply to the data downstream consumers actually read.
    """
    mortgage = mortgage_data.get('RLoan', {})
    terms = mortgage.get('FinancialTerms', {})
    status = mortgage.get('CurrentStatus', {})

    original = terms.get('OriginalLoan')
    current = status.get('OutstandingBalance')
    if original is not None and current is not None and current > original:
        status['OutstandingBalance'] = original * 0.95

    for section, key in ((status, 'CurrentLTV'), (terms, 'OriginalLTV')):
        ltv = section.get(key)
        if ltv is None:
            continue
        if ltv > 100:
            section[key] = 95
        elif ltv < 10:
            section[key] = 60

    for section, key in ((status, 'CurrentInterestRate'), (terms, 'OriginalLendingRate')):
        rate = section.get(key)
        if rate is None:
            continue
        if rate > 15:
            section[key] = 12.0
        elif rate < 1:
            section[key] = 2.0

    return mortgage_data
