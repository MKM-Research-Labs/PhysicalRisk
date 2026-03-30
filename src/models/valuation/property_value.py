# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Property valuation model — deterministic factor tables and calculation.

Multi-factor valuation:
    value = area x price_per_sqm x location_factor
            x age_factor x condition_factor x flood_risk_factor
            x epc_factor x proximity_factor

Each factor table maps a categorical or banded input to a
(min, max) range. The caller supplies the random draw; the model
defines the factor structure.
"""

from typing import Dict, Tuple

from config.models import (
    AGE_BAND_FACTORS,
    BASE_AREA_RANGES,
    BASE_PRICE_PER_SQM,
    CONDITION_FACTORS,
    EPC_FACTORS,
    FLOOD_RISK_FACTORS,
    MAX_PROPERTY_VALUE,
    MIN_PROPERTY_VALUE,
    PROXIMITY_ZONES,
    RENTAL_YIELD_RATES,
    RENT_PER_SQM,
)


def get_age_band(construction_year: int, current_year: int = 2025) -> str:
    """Classify property age into band."""
    age = current_year - construction_year
    if age < 10:
        return 'new_build'
    elif age < 25:
        return 'modern'
    elif age < 50:
        return 'established'
    elif age < 100:
        return 'period'
    else:
        return 'heritage'


def get_proximity_zone(
    distance_to_thames: float,
    flood_risk: str,
) -> str:
    """Classify Thames proximity into zone."""
    if distance_to_thames < 200:
        if flood_risk in ('Very Low', 'Low'):
            return 'close_low_risk'
        else:
            return 'close_high_risk'
    elif distance_to_thames < 500:
        return 'medium'
    else:
        return 'far'


def apply_valuation_factors(
    area: float,
    price_per_sqm: float,
    value_factor: float,
    age_factor: float,
    condition_factor: float,
    flood_risk_factor: float,
    epc_factor: float,
    proximity_factor: float,
    noise_factor: float = 1.0,
) -> float:
    """
    Apply all valuation factors to compute final property value.

    Args:
        area: Floor area in sq meters
        price_per_sqm: Base price per square meter (GBP)
        value_factor: Location-based value multiplier
        age_factor: Construction age adjustment
        condition_factor: Property condition adjustment
        flood_risk_factor: Flood risk discount/premium
        epc_factor: Energy performance adjustment
        proximity_factor: Thames proximity adjustment
        noise_factor: Random variation (default 1.0 = no noise)

    Returns:
        Property value in GBP, clamped to London market bounds
    """
    base_value = area * price_per_sqm * value_factor
    final_value = (base_value
                   * age_factor
                   * condition_factor
                   * flood_risk_factor
                   * epc_factor
                   * proximity_factor
                   * noise_factor)
    return max(MIN_PROPERTY_VALUE, min(MAX_PROPERTY_VALUE, round(final_value, 2)))
