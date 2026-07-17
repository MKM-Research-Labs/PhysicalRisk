# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Financial and gauge reliability risk assessment functions."""

from typing import Any, Dict, Optional


def calculate_value_at_risk(property_value: float, risk_level: str,
                            flood_depth: Optional[float] = None) -> float:
    """
    Calculate the financial value at risk due to flooding.

    Uses depth-based percentage of property value, with risk-level fallback.

    Args:
        property_value: Total property value
        risk_level: Flood risk level string
        flood_depth: Flood depth in meters (optional for more precise calculation)

    Returns:
        Value at risk amount
    """
    if property_value is None or property_value <= 0:
        return 0.0

    risk_percentages = {
        'Very Low': 0.01, 'Very low': 0.01,
        'Low': 0.05,
        'Medium': 0.15,
        'High': 0.35,
        'Very High': 0.60, 'Very high': 0.60,
        'Unknown': 0.10
    }

    base_percentage = risk_percentages.get(risk_level, 0.10)

    if flood_depth is not None and flood_depth > 0:
        if flood_depth > 2.0:
            depth_factor = 0.8
        elif flood_depth > 1.0:
            depth_factor = 0.5
        elif flood_depth > 0.5:
            depth_factor = 0.25
        else:
            depth_factor = 0.1

        final_percentage = max(base_percentage, depth_factor)
    else:
        final_percentage = base_percentage

    return property_value * final_percentage


def assess_gauge_reliability(operational_status: str,
                              last_maintenance: Optional[str] = None,
                              data_frequency: Optional[str] = None) -> Dict[str, Any]:
    """
    Assess the reliability of a flood gauge.

    Args:
        operational_status: Current operational status
        last_maintenance: Date of last maintenance (optional)
        data_frequency: Frequency of data collection (optional)

    Returns:
        Dictionary with reliability assessment
    """
    status_scores = {
        'Fully operational': 95,
        'Maintenance required': 70,
        'Temporarily offline': 30,
        'Decommissioned': 0,
        'Unknown': 50
    }

    reliability_score = status_scores.get(operational_status, 50)

    if data_frequency:
        frequency_adjustments = {
            'real-time': 0,
            'hourly': -5,
            'daily': -15,
            'weekly': -30,
            'monthly': -50
        }

        for freq, adjustment in frequency_adjustments.items():
            if freq in data_frequency.lower():
                reliability_score += adjustment
                break

    if reliability_score >= 90:
        category = "Highly Reliable"
    elif reliability_score >= 70:
        category = "Reliable"
    elif reliability_score >= 50:
        category = "Moderately Reliable"
    elif reliability_score >= 30:
        category = "Low Reliability"
    else:
        category = "Unreliable"

    return {
        'reliability_score': max(0, min(100, reliability_score)),
        'category': category,
        'operational_status': operational_status
    }


def calculate_distance_risk_factor(distance_km: float) -> float:
    """
    Calculate risk factor based on distance to flood source.

    Risk decays with distance: 1.0 at <0.1km to 0.1 at >5km.

    Args:
        distance_km: Distance in kilometers

    Returns:
        Risk factor (0-1, where 1 is highest risk)
    """
    if distance_km is None or distance_km < 0:
        return 0.5

    if distance_km <= 0.1:
        return 1.0
    elif distance_km <= 0.5:
        return 0.8
    elif distance_km <= 1.0:
        return 0.6
    elif distance_km <= 2.0:
        return 0.4
    elif distance_km <= 5.0:
        return 0.2
    else:
        return 0.1


def calculate_insurance_premium_factor(risk_level: str, property_value: float,
                                       flood_depth: Optional[float] = None) -> float:
    """
    Calculate estimated insurance premium factor.

    Premium = base_rate(risk_level) * (1 + depth * 0.5), capped at 10%.

    Args:
        risk_level: Flood risk level
        property_value: Property value
        flood_depth: Flood depth in meters (optional)

    Returns:
        Estimated annual premium as percentage of property value
    """
    base_rates = {
        'Very Low': 0.001, 'Very low': 0.001,
        'Low': 0.002,
        'Medium': 0.005,
        'High': 0.015,
        'Very High': 0.035, 'Very high': 0.035,
        'Unknown': 0.005
    }

    base_rate = base_rates.get(risk_level, 0.005)

    if flood_depth is not None and flood_depth > 0:
        depth_multiplier = 1 + (flood_depth * 0.5)
        base_rate *= depth_multiplier

    return min(base_rate, 0.10)
