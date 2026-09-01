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
Valuation calculations for Thames property random data.

Random sampling layer — all deterministic factor tables and
calculation logic live in models.valuation.
"""

import random
from datetime import datetime
from typing import Any, Dict

from models.valuation.insurance import (
    AGE_PREMIUM_FACTORS,
    BASE_RATE_RANGE,
    CONSTRUCTION_TYPE_FACTORS,
    FLOOD_RISK_PREMIUM_FACTORS,
    PROPERTY_TYPE_PREMIUM_FACTORS,
    apply_insurance_factors,
    get_age_premium_band,
    get_area_premium_factor_range,
)
from models.valuation.property_value import (
    AGE_BAND_FACTORS,
    BASE_AREA_RANGES,
    BASE_PRICE_PER_SQM,
    CONDITION_FACTORS,
    EPC_FACTORS,
    FLOOD_RISK_FACTORS,
    PROXIMITY_ZONES,
    RENT_PER_SQM,
    RENTAL_YIELD_RATES,
    apply_valuation_factors,
    get_age_band,
    get_proximity_zone,
)


def _sample(factor_range):
    """Draw uniform random from (min, max) tuple."""
    return random.uniform(factor_range[0], factor_range[1])


def calculate_property_area(location_info: Dict[str, Any]) -> float:
    """Calculate property floor area based on type and value."""
    property_type = location_info.get('property_type', 'Flat')
    area_range = BASE_AREA_RANGES.get(property_type, (50, 150))
    return round(random.uniform(area_range[0], area_range[1]), 1)


def calculate_property_value(location_info: Dict[str, Any]) -> float:
    """Calculate property value based on location, property type, area, and other factors."""

    property_type = location_info.get('property_type', 'Flat')
    area = location_info.get('property_area', None)
    value_factor = location_info.get('value_factor', 1.0)

    if area is None:
        area = calculate_property_area(location_info)
        location_info['property_area'] = area

    # Sample price per sqm from model table
    psqm_range = BASE_PRICE_PER_SQM.get(property_type, (7000, 7000))
    price_per_sqm = random.uniform(psqm_range[0], psqm_range[1])

    # Age factor
    construction_year = location_info.get('construction_year', random.randint(1950, 2020))
    age_band = get_age_band(construction_year)
    age_factor = _sample(AGE_BAND_FACTORS[age_band])

    # Condition factor
    condition = location_info.get('property_condition', random.choice(
        ['Excellent', 'Good', 'Fair', 'Poor', 'Very poor']))
    condition_factor = _sample(CONDITION_FACTORS.get(condition, (1.0, 1.0)))

    # Flood risk factor
    flood_risk = location_info.get('flood_risk', random.choice(
        ['Very Low', 'Low', 'Medium', 'High', 'Very High']))
    flood_risk_factor = _sample(FLOOD_RISK_FACTORS.get(flood_risk, (1.0, 1.0)))

    # EPC rating factor
    epc_rating = location_info.get('epc_rating', random.choice(
        ['A', 'B', 'C', 'D', 'E', 'F', 'G']))
    epc_factor = _sample(EPC_FACTORS.get(epc_rating, (1.0, 1.0)))

    # Thames proximity factor
    thames_distance = location_info.get('distance_to_thames', 1000)
    prox_zone = get_proximity_zone(thames_distance, flood_risk)
    proximity_factor = _sample(PROXIMITY_ZONES[prox_zone]['range'])

    # Random noise
    noise_factor = random.uniform(0.95, 1.05)

    result = apply_valuation_factors(
        area=area,
        price_per_sqm=price_per_sqm,
        value_factor=value_factor,
        age_factor=age_factor,
        condition_factor=condition_factor,
        flood_risk_factor=flood_risk_factor,
        epc_factor=epc_factor,
        proximity_factor=proximity_factor,
        noise_factor=noise_factor,
    )


    return result


def calculate_sale_price(location_info: Dict[str, Any]) -> float:
    """Calculate historical sale price based on current value and market conditions."""
    current_value = location_info.get('property_value')

    if current_value is None:
        current_value = calculate_property_value(location_info)

    sale_date_str = location_info.get('sale_date')
    if sale_date_str:
        try:
            sale_date = datetime.strptime(sale_date_str, '%Y-%m-%d')
            years_ago = (datetime.now() - sale_date).days / 365.25
        except (ValueError, TypeError):
            years_ago = random.uniform(0.5, 3.0)
    else:
        years_ago = random.uniform(0.5, 3.0)

    if years_ago < 1:
        historical_factor = random.uniform(0.95, 1.05)
    elif years_ago < 2:
        annual_growth = random.uniform(0.02, 0.08)
        historical_factor = (1 + annual_growth) ** (-years_ago)
    else:
        annual_growth = random.uniform(-0.05, 0.12)
        historical_factor = (1 + annual_growth) ** (-years_ago)

    market_condition = random.choice(['boom', 'normal', 'recession'])
    if market_condition == 'boom':
        market_factor = random.uniform(0.85, 0.95)
    elif market_condition == 'recession':
        market_factor = random.uniform(1.05, 1.25)
    else:
        market_factor = random.uniform(0.95, 1.05)

    historical_price = current_value * historical_factor * market_factor
    historical_price = max(50000, min(8000000, historical_price))

    return round(historical_price, 2)


def calculate_monthly_rent(location_info: Dict[str, Any]) -> float:
    """Calculate monthly rent based on property value, area, and local factors."""
    property_value = location_info.get('property_value')
    area = location_info.get('property_area')
    property_type = location_info.get('property_type', 'Flat')

    if property_value is None:
        property_value = calculate_property_value(location_info)

    if area is None:
        area = calculate_property_area(location_info)

    # Rental yield method — tables from model
    yield_range = RENTAL_YIELD_RATES.get(property_type, (0.05, 0.05))
    yield_rate = random.uniform(yield_range[0], yield_range[1])
    rent_from_yield = (property_value * yield_rate) / 12

    # Price per sqm method — tables from model
    sqm_range = RENT_PER_SQM.get(property_type, (30, 30))
    sqm_rate = random.uniform(sqm_range[0], sqm_range[1])
    rent_from_area = area * sqm_rate

    base_rent = (rent_from_yield + rent_from_area) / 2

    value_factor = location_info.get('value_factor', 1.0)
    base_rent *= value_factor

    transport_factor = random.uniform(0.9, 1.2)
    base_rent *= transport_factor

    condition = location_info.get('property_condition', 'Good')
    condition_factor = _sample(CONDITION_FACTORS.get(condition, (1.0, 1.0)))
    base_rent *= condition_factor

    if random.random() < 0.3:
        furnished_factor = random.uniform(1.1, 1.3)
    else:
        furnished_factor = 1.0
    base_rent *= furnished_factor

    demand_factor = random.uniform(0.9, 1.15)
    base_rent *= demand_factor

    base_rent = max(800, min(15000, base_rent))

    return round(base_rent, 2)


def calculate_insurance_premium(location_info: Dict[str, Any]) -> float:
    """Calculate insurance premium based on property value, risk factors, and characteristics."""
    property_value = location_info.get('property_value')
    area = location_info.get('property_area')
    property_type = location_info.get('property_type', 'Flat')

    if property_value is None:
        property_value = calculate_property_value(location_info)

    if area is None:
        area = calculate_property_area(location_info)

    # Base rate from model
    base_rate_per_1000 = random.uniform(BASE_RATE_RANGE[0], BASE_RATE_RANGE[1])

    # Type factor from model table
    type_factor = _sample(PROPERTY_TYPE_PREMIUM_FACTORS.get(property_type, (1.0, 1.0)))

    # Flood risk factor from model table
    flood_risk = location_info.get('flood_risk', 'Low')
    flood_factor = _sample(FLOOD_RISK_PREMIUM_FACTORS.get(flood_risk, (1.0, 1.0)))

    # Age factor from model table
    construction_year = location_info.get('construction_year', 1980)
    age_band = get_age_premium_band(construction_year)
    age_factor = _sample(AGE_PREMIUM_FACTORS[age_band])

    # Construction type factor from model table
    construction_type = location_info.get('construction_type', 'Brick')
    construction_factor = _sample(CONSTRUCTION_TYPE_FACTORS.get(construction_type, (1.0, 1.0)))

    # Area factor from model table
    area_range = get_area_premium_factor_range(area)
    area_factor = _sample(area_range)

    # Security discount
    if random.random() < 0.3:
        security_factor = random.uniform(0.85, 0.95)
    else:
        security_factor = 1.0

    # Claims history
    if random.random() < 0.15:
        claims_factor = random.uniform(1.2, 1.8)
    else:
        claims_factor = random.uniform(0.95, 1.05)

    # Contents premium
    contents_premium = 0.0
    if random.random() < 0.8:
        base_premium = (property_value / 1000) * base_rate_per_1000
        contents_premium = base_premium * random.uniform(0.2, 0.4)

    result = apply_insurance_factors(
        property_value=property_value,
        base_rate_per_1000=base_rate_per_1000,
        type_factor=type_factor,
        flood_factor=flood_factor,
        age_factor=age_factor,
        construction_factor=construction_factor,
        area_factor=area_factor,
        security_factor=security_factor,
        claims_factor=claims_factor,
        contents_premium=contents_premium,
    )


    return result
