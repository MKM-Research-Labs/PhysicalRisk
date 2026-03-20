# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flood risk assessment functions."""

from typing import Any, Dict, Optional

FLOOD_DEPTH_THRESHOLDS = {
    'very_low': 0.0,
    'low': 0.1,
    'medium': 0.5,
    'high': 1.0,
    'very_high': 2.0
}


def assess_flood_risk_level(flood_depth: float) -> str:
    """
    Assess flood risk level based on flood depth.

    Args:
        flood_depth: Flood depth in meters

    Returns:
        Risk level string
    """
    if flood_depth is None or flood_depth < 0:
        return "Unknown"

    if flood_depth <= FLOOD_DEPTH_THRESHOLDS['very_low']:
        return "Very Low"
    elif flood_depth <= FLOOD_DEPTH_THRESHOLDS['low']:
        return "Low"
    elif flood_depth <= FLOOD_DEPTH_THRESHOLDS['medium']:
        return "Medium"
    elif flood_depth <= FLOOD_DEPTH_THRESHOLDS['high']:
        return "High"
    else:
        return "Very High"


def assess_property_vulnerability(ground_elevation: float, flood_level: float,
                                  distance_to_water: Optional[float] = None) -> Dict[str, Any]:
    """
    Assess property vulnerability to flooding.

    Vulnerability score = min(100, depth * 30 + 50_if_flooded + distance_bonus).

    Args:
        ground_elevation: Property elevation in meters
        flood_level: Projected flood level in meters
        distance_to_water: Distance to nearest water body in km (optional)

    Returns:
        Dictionary with vulnerability assessment
    """
    if ground_elevation is None or flood_level is None:
        return {
            'flood_depth': None,
            'risk_level': 'Unknown',
            'vulnerability_score': None,
            'recommendations': ['Insufficient data for assessment']
        }

    flood_depth = max(0, flood_level - ground_elevation)
    risk_level = assess_flood_risk_level(flood_depth)

    vulnerability_score = min(100, (flood_depth * 30) + (50 if flood_depth > 0 else 0))
    if distance_to_water is not None and distance_to_water < 1.0:
        vulnerability_score += 20

    recommendations = _generate_recommendations(flood_depth, risk_level)

    return {
        'flood_depth': flood_depth,
        'risk_level': risk_level,
        'vulnerability_score': min(100, vulnerability_score),
        'recommendations': recommendations
    }


def _generate_recommendations(flood_depth: float, risk_level: str) -> list:
    """Generate recommendations based on flood risk assessment."""
    recommendations = []

    if risk_level in ['High', 'Very High']:
        recommendations.extend([
            "Consider flood insurance if not already covered",
            "Implement flood-resistant modifications",
            "Develop an emergency evacuation plan",
            "Install flood barriers or waterproofing"
        ])
        if flood_depth > 1.0:
            recommendations.extend([
                "Consider relocating utilities to higher floors",
                "Install flood vents in foundation walls",
                "Elevate critical equipment and furnaces"
            ])
    elif risk_level == 'Medium':
        recommendations.extend([
            "Review flood insurance options",
            "Monitor local flood warnings",
            "Prepare emergency supplies",
            "Consider minor flood-proofing measures"
        ])
    elif risk_level == 'Low':
        recommendations.extend([
            "Stay informed about local flood risks",
            "Maintain awareness of seasonal variations",
            "Consider basic emergency preparedness"
        ])
    else:
        recommendations.extend([
            "Monitor changes in local flood risk",
            "Stay informed about climate projections"
        ])

    return recommendations
