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

"""
Insurance premium model — deterministic factor tables and calculation.

Multi-factor premium:
    premium = (property_value / 1000) x base_rate
              x type_factor x flood_factor x age_factor
              x construction_factor x area_factor
              x security_factor x claims_factor

Each factor table maps a categorical or banded input to a
(min, max) range. The caller supplies the random draw; the model
defines the factor structure.
"""

from typing import Dict, Tuple

from config.models import (
    AGE_PREMIUM_FACTORS,
    AREA_PREMIUM_BANDS,
    BASE_RATE_RANGE,
    CONSTRUCTION_TYPE_FACTORS,
    FLOOD_RISK_PREMIUM_FACTORS,
    MAX_PREMIUM,
    MIN_PREMIUM,
    PROPERTY_TYPE_PREMIUM_FACTORS,
)


def get_age_premium_band(construction_year: int, current_year: int = 2025) -> str:
    """Classify property age into insurance premium band."""
    age = current_year - construction_year
    if age < 10:
        return 'new_build'
    elif age < 30:
        return 'modern'
    elif age < 100:
        return 'established'
    else:
        return 'heritage'


def get_area_premium_factor_range(area: float) -> Tuple[float, float]:
    """Get premium factor range for floor area."""
    for threshold, factor_range in AREA_PREMIUM_BANDS:
        if area < threshold:
            return factor_range
    return AREA_PREMIUM_BANDS[-1][1]


def apply_insurance_factors(
    property_value: float,
    base_rate_per_1000: float,
    type_factor: float,
    flood_factor: float,
    age_factor: float,
    construction_factor: float,
    area_factor: float,
    security_factor: float = 1.0,
    claims_factor: float = 1.0,
    contents_premium: float = 0.0,
) -> float:
    """
    Apply all insurance premium factors.

    Args:
        property_value: Property value in GBP
        base_rate_per_1000: Base premium rate per GBP 1,000
        type_factor: Property type multiplier
        flood_factor: Flood risk multiplier
        age_factor: Building age multiplier
        construction_factor: Construction type multiplier
        area_factor: Floor area multiplier
        security_factor: Security discount (default 1.0)
        claims_factor: Claims history multiplier (default 1.0)
        contents_premium: Additional contents premium (default 0.0)

    Returns:
        Annual premium in GBP, clamped to bounds
    """
    base_premium = (property_value / 1000) * base_rate_per_1000
    final_premium = (base_premium
                     * type_factor
                     * flood_factor
                     * age_factor
                     * construction_factor
                     * area_factor
                     * security_factor
                     * claims_factor)
    final_premium += contents_premium
    return max(MIN_PREMIUM, min(MAX_PREMIUM, round(final_premium, 2)))
