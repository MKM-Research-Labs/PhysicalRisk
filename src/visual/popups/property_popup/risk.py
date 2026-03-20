# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Property popup risk — risk summary and colour functions."""


def get_mortgage_risk_summary(flood_risk_level: str, mortgage_value: float,
                              loan_amount: float, ltv_ratio: float) -> str:
    """Generate a summary assessment of mortgage risk."""
    if flood_risk_level in ['High', 'Very High']:
        return "High Risk - Significant flood exposure threatening mortgage value"

    if mortgage_value < 0:
        negative_pct = abs(mortgage_value) / loan_amount
        if negative_pct > 0.1:
            return "Critical Risk - Mortgage value severely impacted"
        elif negative_pct > 0.05:
            return "High Risk - Significant negative impact on mortgage value"
        elif negative_pct > 0.02:
            return "Moderate Risk - Some negative impact on mortgage value"

    if ltv_ratio > 0.8 and flood_risk_level in ['Medium', 'High', 'Very High']:
        return "High Risk - High LTV with flood exposure"
    elif ltv_ratio > 0.7 and flood_risk_level in ['Medium', 'High']:
        return "Moderate Risk - Elevated LTV with some flood exposure"

    if flood_risk_level == 'Medium':
        return "Moderate Risk - Some flood exposure"
    elif flood_risk_level == 'Low':
        return "Low Risk - Limited flood exposure"
    else:
        return "Minimal Risk - No significant flood impact identified"


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
