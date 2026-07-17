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
Location-based generators for Thames property random data.

Postcodes, street names, bedrooms, bathrooms, floor levels, council tax bands.
"""

import random
from typing import Any, Dict


def generate_bedrooms(location_info: Dict[str, Any]) -> int:
    """
    Generate realistic bedroom count based on property type.

    Flats: 1-3 bedrooms (studio, 1-bed, 2-bed, occasional 3-bed)
    Houses: 2-5 bedrooms
    """
    property_type = location_info.get('property_type', 'Flat')

    if property_type == 'Flat':
        return random.choices([1, 2, 3], weights=[30, 50, 20])[0]
    else:
        return random.choices([2, 3, 4, 5], weights=[15, 40, 35, 10])[0]


def generate_bathrooms(location_info: Dict[str, Any]) -> int:
    """
    Generate realistic bathroom count based on property type and bedrooms.

    Typically: 1 bathroom for small properties, 2+ for larger
    """
    property_type = location_info.get('property_type', 'Flat')
    bedrooms = location_info.get('bedrooms', 2)

    if property_type == 'Flat':
        return 1 if bedrooms <= 2 else random.choices([1, 2], weights=[70, 30])[0]
    else:
        if bedrooms <= 2:
            return 1
        elif bedrooms == 3:
            return random.choices([1, 2], weights=[60, 40])[0]
        else:
            return random.choices([2, 3], weights=[70, 30])[0]


def generate_floor_level(location_info: Dict[str, Any]) -> float:
    """
    Generate realistic floor level in meters.

    Ground floor: 0-0.5m
    Upper floors: 3m per floor, up to ~15m for typical buildings
    """
    property_type = location_info.get('property_type', 'Flat')

    if property_type == 'Flat':
        floor_number = random.choices([0, 1, 2, 3, 4, 5], weights=[25, 25, 20, 15, 10, 5])[0]
        base_height = floor_number * 3.0
        variation = random.uniform(-0.3, 0.3)
        return round(base_height + variation, 2)
    else:
        return round(random.uniform(0.0, 0.5), 2)


def generate_postcode_for_area(location_info: Dict[str, Any]) -> str:
    """
    Generate a realistic London postcode based on area.

    Uses proper London postcode districts.
    """
    area_name = location_info.get('area_name', 'Chelsea')

    postcode_prefixes = {
        'Chelsea': ['SW3', 'SW10'],
        'Kensington': ['W8', 'SW7'],
        'Westminster': ['SW1', 'W1'],
        'Camden': ['NW1', 'NW3'],
        'Islington': ['N1', 'N7'],
        'Hackney': ['E8', 'E9'],
        'Tower Hamlets': ['E1', 'E14'],
        'Southwark': ['SE1', 'SE17'],
        'Lambeth': ['SW9', 'SE11'],
        'Wandsworth': ['SW18', 'SW11'],
        'Greenwich': ['SE10', 'SE3'],
        'Lewisham': ['SE13', 'SE6'],
        'Hammersmith': ['W6', 'W12'],
        'Fulham': ['SW6', 'SW10'],
        'Richmond': ['TW9', 'TW10'],
    }

    prefix = random.choice(postcode_prefixes.get(area_name, ['SW1', 'N1', 'E1', 'SE1', 'W1']))
    sector = random.randint(1, 9)
    unit = ''.join(random.choices('ABDEFGHJLNPQRSTUWXYZ', k=2))

    return f"{prefix} {sector}{unit}"


def generate_street_name(location_info: Dict[str, Any]) -> str:
    """
    Generate realistic street name from Thames street data.

    The STREETS data should be passed through location_info by the generator.
    """
    area_name = location_info.get('area_name', 'Chelsea')

    streets_data = location_info.get('streets_data', {})
    if area_name in streets_data:
        return random.choice(streets_data[area_name])

    street_names = [
        'High Street', 'Church Road', 'Station Road', 'Park Road',
        'Victoria Road', 'King Street', 'Queen Street', 'London Road',
        'Mill Lane', 'Chapel Street', 'The Avenue', 'Manor Road'
    ]
    return random.choice(street_names)


def calculate_purchase_price(location_info: Dict[str, Any]) -> float:
    """
    Generate realistic purchase price based on property value.

    Purchase price is typically 85-100% of current property value,
    representing historical purchase at slightly different market conditions.
    """
    property_value = location_info.get('property_value', 500000)
    multiplier = random.uniform(0.85, 1.00)
    purchase_price = property_value * multiplier
    return round(purchase_price, 2)


def generate_council_tax_band(location_info: Dict[str, Any]) -> str:
    """
    Generate council tax band based on property value.

    UK Council Tax bands (1991 values scaled ~3x for current market).
    """
    property_value = location_info.get('property_value', 500000)

    if property_value < 120000:
        return 'A'
    elif property_value < 156000:
        return 'B'
    elif property_value < 204000:
        return 'C'
    elif property_value < 264000:
        return 'D'
    elif property_value < 360000:
        return 'E'
    elif property_value < 480000:
        return 'F'
    elif property_value < 960000:
        return 'G'
    else:
        return 'H'
