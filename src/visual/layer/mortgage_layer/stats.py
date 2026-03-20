# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Mortgage portfolio statistics computation."""

from typing import Any, Dict, List

import numpy as np


def get_mortgage_statistics(mortgage_locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for mortgages.

    Args:
        mortgage_locations: List of mortgage location data

    Returns:
        Dictionary with mortgage statistics
    """
    if not mortgage_locations:
        return {}

    loan_amounts = []
    ltv_ratios = []
    risk_levels = []

    for location in mortgage_locations:
        mortgage_info = location['mortgage_info']
        mortgage_risk_info = location['mortgage_risk_info']

        loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
        if loan_amount and loan_amount > 0:
            loan_amounts.append(float(loan_amount))

        ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
        if ltv_ratio:
            if ltv_ratio > 1:
                ltv_ratio = ltv_ratio / 100
            ltv_ratios.append(ltv_ratio)

        if mortgage_risk_info:
            risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
            risk_levels.append(risk_level)

    stats = {
        'total_mortgages': len(mortgage_locations),
        'avg_loan_amount': np.mean(loan_amounts) if loan_amounts else 0,
        'total_loan_value': sum(loan_amounts) if loan_amounts else 0,
        'avg_ltv_ratio': np.mean(ltv_ratios) if ltv_ratios else 0,
        'high_ltv_count': len([r for r in ltv_ratios if r > 0.8]),
    }

    risk_counts = {}
    for risk in risk_levels:
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    stats['risk_distribution'] = risk_counts

    return stats
