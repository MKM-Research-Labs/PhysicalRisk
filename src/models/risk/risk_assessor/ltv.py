# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""LTV and mortgage risk assessment functions."""

from typing import Optional

LTV_RISK_THRESHOLDS = {
    'low': 0.6,
    'moderate': 0.8,
    'high': 0.95,
    'critical': 1.0
}


def assess_ltv_risk_level(ltv_ratio: float) -> str:
    """
    Assess loan-to-value risk level.

    Args:
        ltv_ratio: LTV ratio (0-1 or 0-100)

    Returns:
        Risk level string
    """
    if ltv_ratio is None:
        return "Unknown"

    if ltv_ratio > 1:
        ltv_ratio = ltv_ratio / 100

    if ltv_ratio <= LTV_RISK_THRESHOLDS['low']:
        return "Low"
    elif ltv_ratio <= LTV_RISK_THRESHOLDS['moderate']:
        return "Moderate"
    elif ltv_ratio <= LTV_RISK_THRESHOLDS['high']:
        return "High"
    else:
        return "Critical"


def assess_mortgage_risk(flood_risk_level: str, mortgage_value: float,
                         loan_amount: float, ltv_ratio: float) -> str:
    """
    Generate a comprehensive mortgage risk assessment.

    Args:
        flood_risk_level: The flood risk level for the property
        mortgage_value: The calculated value of the mortgage
        loan_amount: The original loan amount
        ltv_ratio: Loan-to-value ratio

    Returns:
        Risk assessment string
    """
    if flood_risk_level in ['High', 'Very High']:
        return "High Risk - Significant flood exposure threatening mortgage value"

    if mortgage_value is not None and loan_amount is not None and mortgage_value < 0:
        negative_pct = abs(mortgage_value) / loan_amount if loan_amount > 0 else 0

        if negative_pct > 0.1:
            return "Critical Risk - Mortgage value severely impacted"
        elif negative_pct > 0.05:
            return "High Risk - Significant negative impact on mortgage value"
        elif negative_pct > 0.02:
            return "Moderate Risk - Some negative impact on mortgage value"

    if ltv_ratio is not None:
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


def calculate_combined_risk_score(flood_risk_level: str, ltv_ratio: float,
                                  property_age: Optional[int] = None,
                                  construction_type: Optional[str] = None) -> float:
    """
    Calculate a combined risk score considering multiple factors.

    Score = flood_score x ltv_multiplier x age_factor x construction_factor, capped at 10.

    Args:
        flood_risk_level: Flood risk level string
        ltv_ratio: Loan-to-value ratio
        property_age: Age of property in years (optional)
        construction_type: Type of construction (optional)

    Returns:
        Combined risk score (0-10 scale)
    """
    flood_scores = {
        'Very Low': 1, 'Very low': 1,
        'Low': 2,
        'Medium': 4,
        'High': 7,
        'Very High': 9, 'Very high': 9,
        'Unknown': 3
    }

    flood_score = flood_scores.get(flood_risk_level, 3)

    ltv_multiplier = 1.0
    if ltv_ratio is not None:
        if ltv_ratio > 1:
            ltv_ratio = ltv_ratio / 100

        if ltv_ratio > 0.95:
            ltv_multiplier = 2.0
        elif ltv_ratio > 0.8:
            ltv_multiplier = 1.5
        elif ltv_ratio > 0.6:
            ltv_multiplier = 1.2

    age_factor = 1.0
    if property_age is not None:
        if property_age > 100:
            age_factor = 1.3
        elif property_age > 50:
            age_factor = 1.1

    construction_factor = 1.0
    if construction_type:
        construction_risks = {
            'timber': 1.3, 'wood': 1.3,
            'brick': 1.0,
            'concrete': 0.9,
            'steel': 0.8
        }
        construction_factor = construction_risks.get(
            construction_type.lower(), 1.0
        )

    combined_score = flood_score * ltv_multiplier * age_factor * construction_factor
    return min(combined_score, 10.0)
