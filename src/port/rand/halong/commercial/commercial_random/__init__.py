# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Hanoi-style commercial asset random value generators.

Most fields overlap with residential — for those we delegate to
``property_random``. Commercial-specific menus and per-type sizing live in:

constants.py — type allocation + per-type parameter tables
metadata.py — id / type / area / value sizing per index
generators.py — commercial-only field generators + dispatcher

Type allocation for the first 10-asset run:

indices 0-2 Office (3)
indices 3-5 MultiFamily (3)
index 6 Hotel (1)
indices 7-8 Retail (2)
index 9 MixedUse (1)
"""

from .constants import (  # noqa: F401
    ANCHOR_TENANT_POOL,
    COMMERCIAL_CONSTRUCTION_TYPES,
    COMMERCIAL_TYPE_ALLOCATION,
    TYPE_AREA_RANGE,
    TYPE_BUSINESS_RATES,
    TYPE_LOADING_BAYS,
    TYPE_PARKING_SPACES,
    TYPE_STOREYS,
    TYPE_TOTAL_UNITS,
    TYPE_USE_CLASS,
    TYPE_VALUE_PER_SQM,
)

from .generators import generate_field_value  # noqa: F401
from .metadata import (  # noqa: F401
    anchor_tenant,
    generate_commercial_metadata,
    get_commercial_type,
    period_from_year,
)

generate_property_metadata = generate_commercial_metadata

__all__ = [
    "ANCHOR_TENANT_POOL",
    "COMMERCIAL_CONSTRUCTION_TYPES",
    "COMMERCIAL_TYPE_ALLOCATION",
    "TYPE_AREA_RANGE",
    "TYPE_BUSINESS_RATES",
    "TYPE_LOADING_BAYS",
    "TYPE_PARKING_SPACES",
    "TYPE_STOREYS",
    "TYPE_TOTAL_UNITS",
    "TYPE_USE_CLASS",
    "TYPE_VALUE_PER_SQM",
    "anchor_tenant",
    "generate_commercial_metadata",
    "generate_field_value",
    "generate_property_metadata",
    "get_commercial_type",
    "period_from_year",
]
