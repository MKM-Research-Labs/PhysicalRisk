# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Property popup risk — risk summary and colour functions."""

from models.risk.risk_assessor.ltv import assess_mortgage_risk


def get_mortgage_risk_summary(flood_risk_level: str, mortgage_value: float,
                              loan_amount: float, ltv_ratio: float) -> str:
    """Generate a summary assessment of mortgage risk.

    Delegates to :func:`models.risk.risk_assessor.ltv.assess_mortgage_risk`.
    """
    return assess_mortgage_risk(flood_risk_level, mortgage_value,
                                loan_amount, ltv_ratio)


def get_overall_risk_color(flood_risk_level: str, mortgage_value: float,
                           loan_amount: float, ltv_ratio: float) -> str:
    """Determine risk color based on flood risk level and mortgage value."""
    if flood_risk_level in ['High', 'Very High'] or (
            mortgage_value < 0 and abs(mortgage_value) > loan_amount * 0.05):
        return "red"
    elif flood_risk_level == 'Medium' or (
            mortgage_value < 0 and abs(mortgage_value) > loan_amount * 0.02):
        return "orange"
    elif flood_risk_level == 'Low':
        return "goldenrod"
    else:
        return "green"
