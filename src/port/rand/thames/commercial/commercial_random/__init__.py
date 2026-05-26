# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Thames-specific commercial asset random value generators.

Most fields overlap with residential — for those we delegate to
``port.rand.thames.property.property_random``. Commercial-specific menus
and per-type sizing live in this module.

Type allocation for the first 10-asset run (user-requested mix):

    indices 0-2  Office       (3)
    indices 3-5  MultiFamily  (3)   — apartment blocks / BTR
    index   6    Hotel        (1)
    indices 7-8  Retail       (2)
    index   9    MixedUse     (1)
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from port.rand.thames.property import property_random as _resi_random


# --- Per-type allocation + parameterisation --------------------------------

COMMERCIAL_TYPE_ALLOCATION = [
    "Office", "Office", "Office",
    "MultiFamily", "MultiFamily", "MultiFamily",
    "Hotel",
    "Retail", "Retail",
    "MixedUse",
]

# (min_sqm, max_sqm) — gross internal area
_TYPE_AREA_RANGE = {
    "Office":      (1500, 30000),
    "MultiFamily": (3000, 25000),
    "Hotel":       (4000, 35000),
    "Retail":      (500, 8000),
    "MixedUse":    (2500, 20000),
}

# £/sqm capital value
_TYPE_VALUE_PER_SQM = {
    "Office":      (8000, 15000),
    "MultiFamily": (5000, 10000),
    "Hotel":       (6000, 12000),
    "Retail":      (4000, 12000),
    "MixedUse":    (6000, 12000),
}

_TYPE_USE_CLASS = {
    "Office":      "E(g)(i)",
    "MultiFamily": "C3",
    "Hotel":       "C1",
    "Retail":      "E(a)",
    "MixedUse":    "E + C3",
}

_TYPE_BUSINESS_RATES = {
    "Office":      "Office",
    "MultiFamily": "Other",
    "Hotel":       "Hotel",
    "Retail":      "Shop and Premises",
    "MixedUse":    "Mixed",
}

# (min_storeys, max_storeys)
_TYPE_STOREYS = {
    "Office":      (4, 25),
    "MultiFamily": (4, 20),
    "Hotel":       (4, 30),
    "Retail":      (1, 4),
    "MixedUse":    (3, 15),
}

_TYPE_TOTAL_UNITS = {
    "Office":      (1, 5),
    "MultiFamily": (30, 200),
    "Hotel":       (50, 350),
    "Retail":      (1, 12),
    "MixedUse":    (5, 100),
}

_TYPE_PARKING_SPACES = {
    "Office":      (20, 200),
    "MultiFamily": (10, 150),
    "Hotel":       (30, 200),
    "Retail":      (50, 400),
    "MixedUse":    (20, 150),
}

_TYPE_LOADING_BAYS = {
    "Office":      (0, 2),
    "MultiFamily": (0, 2),
    "Hotel":       (1, 4),
    "Retail":      (2, 8),
    "MixedUse":    (1, 4),
}

# Construction options applicable to commercial buildings (steel/concrete
# frame dominate; the residential menu includes them).
_COMMERCIAL_CONSTRUCTION = ["Steel frame", "Concrete frame", "Brick and block",
                            "Modern methods", "Mixed construction"]


def get_commercial_type(index: int) -> str:
    """Return the allocated CommercialType for a given index."""
    if index < len(COMMERCIAL_TYPE_ALLOCATION):
        return COMMERCIAL_TYPE_ALLOCATION[index]
    # Beyond the fixed allocation, cycle through.
    return COMMERCIAL_TYPE_ALLOCATION[index % len(COMMERCIAL_TYPE_ALLOCATION)]


def _deterministic_commercial_id(location: Dict[str, Any], index: int) -> str:
    """Stable CPROP-xxxxxxxx id derived from location + index."""
    seed = f"{location.get('name','')}|{location.get('vertical_offset','')}|{index}"
    h = hashlib.md5(seed.encode()).hexdigest()[:8]
    return f"CPROP-{h}"


# --- Public API: metadata + field-value generation --------------------------

def generate_commercial_metadata(index: int, location: Dict[str, Any]) -> Dict[str, Any]:
    """Generate metadata for a single commercial asset."""
    ctype = get_commercial_type(index)
    area = round(random.uniform(*_TYPE_AREA_RANGE[ctype]), 0)
    value_per_sqm = random.uniform(*_TYPE_VALUE_PER_SQM[ctype])
    value_factor = location.get('value_factor', 1.0)
    value = round(area * value_per_sqm * value_factor, -3)
    construction_year = random.randint(1880, datetime.now().year - 1)

    return {
        'property_id': _deterministic_commercial_id(location, index),
        'commercial_type': ctype,
        'property_type': ctype,   # alias for residential generators that look up 'property_type'
        'construction_year': construction_year,
        'property_area': area,
        'property_value': value,
        'elevation': location['elevation'],
        'vertical_offset': location.get('vertical_offset', 0.5),
        'area_name': location.get('name', 'Unknown'),
        'value_factor': value_factor,
        'streets_data': location.get('streets_data', {}),
    }


def _commercial_generators() -> Dict[str, Callable]:
    """Lambdas for commercial-only fields. info is the location_info dict
    built inside generate_field_value below (includes commercial_type)."""
    return {
        "CommercialType":         lambda info: info["commercial_type"],
        "UseClassUKO":            lambda info: _TYPE_USE_CLASS[info["commercial_type"]],
        "BusinessRatesCategory":  lambda info: _TYPE_BUSINESS_RATES[info["commercial_type"]],
        "OccupancyStatus":        lambda info: random.choices(
            ["Fully occupied", "Partially vacant", "Vacant"], weights=[0.7, 0.25, 0.05])[0],
        "PropertyAreaSqm":        lambda info: info["property_area"],
        "NetInternalAreaSqm":     lambda info: round(info["property_area"] * random.uniform(0.82, 0.92), 0),
        "NetLettableAreaSqm":     lambda info: round(info["property_area"] * random.uniform(0.80, 0.90), 0),
        "PropertyValue":          lambda info: info["property_value"],
        "NumberOfStoreys":        lambda info: random.randint(*_TYPE_STOREYS[info["commercial_type"]]),
        "TotalUnits":             lambda info: random.randint(*_TYPE_TOTAL_UNITS[info["commercial_type"]]),
        "ParkingSpaces":          lambda info: random.randint(*_TYPE_PARKING_SPACES[info["commercial_type"]]),
        "LoadingBays":            lambda info: random.randint(*_TYPE_LOADING_BAYS[info["commercial_type"]]),
        "PlantRoomLocation":      lambda info: random.choice(["Basement", "Ground floor", "Roof", "External"]),
        "ServiceCore":            lambda info: random.choice(["Central core", "Multiple cores", "External core", "None"]),
        "ConstructionType":       lambda info: random.choice(_COMMERCIAL_CONSTRUCTION),
        "ConstructionYear":       lambda info: info["construction_year"],
        "PropertyPeriod":         lambda info: _period_from_year(info["construction_year"]),
        "PropertyCondition":      lambda info: random.choices(
            ["Excellent", "Good", "Fair", "Poor", "Very poor"],
            weights=[0.15, 0.45, 0.25, 0.10, 0.05])[0],

        # AccessibilityFeatures
        "DisabledAccess":         lambda info: random.random() < 0.85,
        "GoodsLiftCount":         lambda info: random.randint(0, 3),
        "GoodsLiftCapacityKg":    lambda info: float(random.choice([1000, 1600, 2500, 3500])),
        "EmergencyExits":         lambda info: max(2, int(info["property_area"] / 1500)),
        "DeliveryBays":           lambda info: random.randint(*_TYPE_LOADING_BAYS[info["commercial_type"]]),

        # Tenancy
        "AnchorTenant":           lambda info: _anchor_tenant(info["commercial_type"]),
        "WAULT":                  lambda info: round(random.uniform(2.0, 12.0), 1),
        "ServiceChargeGbpPerSqm": lambda info: round(random.uniform(40, 120), 2),
        "NetInitialYield":        lambda info: round(random.uniform(0.035, 0.085), 4),
        "EquivalentYield":        lambda info: round(random.uniform(0.040, 0.090), 4),
        "ReversionaryYield":      lambda info: round(random.uniform(0.045, 0.095), 4),
        "CovenantStrength":       lambda info: random.choices(
            ["AAA", "AA", "A", "BBB", "BB", "B", "Unrated"],
            weights=[0.05, 0.10, 0.30, 0.30, 0.15, 0.05, 0.05])[0],
    }


def _period_from_year(year: int) -> str:
    if year < 1919: return "Pre-1919"
    if year < 1945: return "1919-1944"
    if year < 1976: return "1945-1975"
    if year < 2000: return "1976-1999"
    if year < 2009: return "2000-2008"
    return "2009-Present"


_ANCHOR_TENANT_POOL = {
    "Office": ["Multi-let", "Multi-let", "Deloitte", "PwC", "Linklaters",
               "BlackRock", "Bloomberg", "Government Property Agency"],
    "MultiFamily": ["Multi-let"],
    "Hotel": ["IHG", "Marriott", "Accor", "Hilton", "Premier Inn",
              "Travelodge", "Mandarin Oriental"],
    "Retail": ["John Lewis", "Tesco", "Sainsbury's", "Boots",
               "Marks & Spencer", "Pret A Manger", "Multi-let"],
    "MixedUse": ["Multi-let"],
}


def _anchor_tenant(commercial_type: str) -> str:
    pool = _ANCHOR_TENANT_POOL.get(commercial_type, ["Multi-let"])
    return random.choice(pool)


def generate_field_value(field_name: str, field_def: Dict, index: int,
                         metadata: Dict[str, Any]) -> Any:
    """Generate a value for a commercial schema field.

    Tries commercial-specific generators first, falls back to the residential
    property_random generators, then to type-based defaults.
    """
    info = {
        'commercial_type':  metadata.get('commercial_type'),
        'property_type':    metadata.get('commercial_type'),
        'property_area':    metadata.get('property_area'),
        'property_value':   metadata.get('property_value'),
        'construction_year': metadata.get('construction_year'),
        'elevation':        metadata.get('elevation'),
        'vertical_offset':  metadata.get('vertical_offset', 0.5),
        'area_name':        metadata.get('area_name'),
        'value_factor':     metadata.get('value_factor', 1.0),
        'streets_data':     metadata.get('streets_data', {}),
    }

    commercial_gens = _commercial_generators()
    if field_name in commercial_gens:
        try:
            return commercial_gens[field_name](info)
        except Exception:
            pass

    # Delegate to residential generators for everything we share (Location,
    # RiskAssessment, ResilienceMeasures, EnergyPerformance, ratings, etc.).
    return _resi_random.generate_field_value(field_name, field_def, index, metadata)


# Convenience exposed for parity with property_random.
generate_property_metadata = generate_commercial_metadata


__all__ = [
    "COMMERCIAL_TYPE_ALLOCATION",
    "get_commercial_type",
    "generate_commercial_metadata",
    "generate_property_metadata",
    "generate_field_value",
]
