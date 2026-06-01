# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Metadata generation for commercial assets — id, type allocation,
area + value sizing, period mapping, anchor-tenant pool draws."""

import hashlib
import random
from datetime import datetime
from typing import Any, Dict

from port.rand.halong.commercial.bri_codes import for_commercial as _bri_for_commercial

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
    seed = f"{location.get('name', '')}|{location.get('vertical_offset', '')}|{index}"
    h = hashlib.md5(seed.encode()).hexdigest()[:8]
    return f"CPROP-{h}"

def period_from_year(year: int) -> str:
    """Map a construction year to a simple period bucket."""
    if year < 1980:
        return "Pre-1980"
    if year < 1995:
        return "1980-1994"
    if year < 2005:
        return "1995-2004"
    if year < 2015:
        return "2005-2014"
    return "2015-Present"

def anchor_tenant(commercial_type: str) -> str:
    """Draw an anchor tenant from the per-type pool."""
    pool = ANCHOR_TENANT_POOL.get(commercial_type, ["Multi-let"])
    return random.choice(pool)

def _construction_year_for_type(commercial_type: str) -> int:
    """Broad Hanoi-plausible year bands by commercial archetype."""
    current_year = datetime.now().year - 1

    year_bands = {
        "Office": [
            ((1995, 2004), 0.15),
            ((2005, 2014), 0.45),
            ((2015, current_year), 0.40),
        ],
        "MultiFamily": [
            ((1995, 2004), 0.10),
            ((2005, 2014), 0.40),
            ((2015, current_year), 0.50),
        ],
        "Hotel": [
            ((1995, 2004), 0.10),
            ((2005, 2014), 0.35),
            ((2015, current_year), 0.55),
        ],
        "Retail": [
            ((1985, 1994), 0.15),
            ((1995, 2004), 0.25),
            ((2005, 2014), 0.35),
            ((2015, current_year), 0.25),
        ],
        "MixedUse": [
            ((2000, 2009), 0.20),
            ((2010, 2017), 0.45),
            ((2018, current_year), 0.35),
        ],
    }

    bands = year_bands.get(commercial_type, [((2005, current_year), 1.0)])
    ranges = [b[0] for b in bands]
    weights = [b[1] for b in bands]
    start, end = random.choices(ranges, weights=weights, k=1)[0]
    return random.randint(start, end)

def generate_commercial_metadata(index: int, location: Dict[str, Any]) -> Dict[str, Any]:
    """Build the metadata dict for a single commercial asset."""
    ctype = get_commercial_type(index)
    area = round(random.uniform(*TYPE_AREA_RANGE[ctype]), 0)
    value_per_sqm = random.uniform(*TYPE_VALUE_PER_SQM[ctype])
    value_factor = location.get("value_factor", 1.0)
    value = round(area * value_per_sqm * value_factor, -3)
    construction_year = _construction_year_for_type(ctype)

    return {
        "property_id": _deterministic_commercial_id(location, index),
        "commercial_type": ctype,
        "property_type": ctype,
        "construction_year": construction_year,
        "property_area": area,
        "property_value": value,
        "elevation": location["elevation"],
        "vertical_offset": location.get("vertical_offset", 0.5),
        "area_name": location.get("name", "Unknown"),
        "value_factor": value_factor,
        "streets_data": location.get("streets_data", {}),
        "bri_prototype": _bri_for_commercial(ctype),
    }
