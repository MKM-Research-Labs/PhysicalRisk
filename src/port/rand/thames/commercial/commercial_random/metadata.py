# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Metadata generation for commercial assets — id, type allocation,
area + value sizing, period mapping, anchor-tenant pool draws."""

import hashlib
import random
from datetime import datetime
from typing import Any, Dict

from .constants import (
    ANCHOR_TENANT_POOL,
    COMMERCIAL_TYPE_ALLOCATION,
    TYPE_AREA_RANGE,
    TYPE_VALUE_PER_SQM,
)


def get_commercial_type(index: int) -> str:
    """Return the allocated CommercialType for a given index.

    Cycles past the fixed first-slice mix once we exceed its length.
    """
    if index < len(COMMERCIAL_TYPE_ALLOCATION):
        return COMMERCIAL_TYPE_ALLOCATION[index]
    return COMMERCIAL_TYPE_ALLOCATION[index % len(COMMERCIAL_TYPE_ALLOCATION)]


def _deterministic_commercial_id(location: Dict[str, Any], index: int) -> str:
    """Stable CPROP-xxxxxxxx id derived from location + index."""
    seed = f"{location.get('name','')}|{location.get('vertical_offset','')}|{index}"
    h = hashlib.md5(seed.encode()).hexdigest()[:8]
    return f"CPROP-{h}"


def period_from_year(year: int) -> str:
    """Map a construction year to its PropertyPeriod menu value."""
    if year < 1919:
        return "Pre-1919"
    if year < 1945:
        return "1919-1944"
    if year < 1976:
        return "1945-1975"
    if year < 2000:
        return "1976-1999"
    if year < 2009:
        return "2000-2008"
    return "2009-Present"


def anchor_tenant(commercial_type: str) -> str:
    """Draw an anchor tenant from the per-type pool. 'Multi-let' is the
    fallback for unknown asset classes."""
    pool = ANCHOR_TENANT_POOL.get(commercial_type, ["Multi-let"])
    return random.choice(pool)


def generate_commercial_metadata(index: int, location: Dict[str, Any]) -> Dict[str, Any]:
    """Build the metadata dict for a single commercial asset.

    Output keys are a superset of property_random.generate_property_metadata
    so the shared schema walker and residential delegators read them
    transparently. ``commercial_type`` is set deterministically by index
    (see ``COMMERCIAL_TYPE_ALLOCATION``); area + value scale to the asset
    class via the per-type tables.
    """
    ctype = get_commercial_type(index)
    area = round(random.uniform(*TYPE_AREA_RANGE[ctype]), 0)
    value_per_sqm = random.uniform(*TYPE_VALUE_PER_SQM[ctype])
    value_factor = location.get('value_factor', 1.0)
    value = round(area * value_per_sqm * value_factor, -3)
    construction_year = random.randint(1880, datetime.now().year - 1)

    return {
        'property_id': _deterministic_commercial_id(location, index),
        'commercial_type': ctype,
        # 'property_type' alias is required by residential generators that
        # look up location_info['property_type'].
        'property_type': ctype,
        'construction_year': construction_year,
        'property_area': area,
        'property_value': value,
        'elevation': location['elevation'],
        'vertical_offset': location.get('vertical_offset', 0.5),
        'area_name': location.get('name', 'Unknown'),
        'value_factor': value_factor,
        'streets_data': location.get('streets_data', {}),
    }
