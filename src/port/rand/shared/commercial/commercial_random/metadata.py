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

"""Metadata generation for commercial assets — id, type allocation, area +
value sizing, period mapping, anchor-tenant draws.

Catchment-agnostic: every per-catchment value (archetype mix, area/value
ranges, period buckets, tenant pools, construction-year strategy) is read
from the active catchment profile (``port.rand.profiles.active_profile()``).
"""

import hashlib
import random
from datetime import datetime
from typing import Any, Dict

from port.rand.profiles import active_profile
from port.rand.shared.commercial.bri_codes import for_commercial as _bri_for_commercial


def get_commercial_type(index: int) -> str:
    """Return the allocated CommercialType for a given index.

    Cycles past the fixed first-slice mix once we exceed its length.
    """
    alloc = active_profile().COMMERCIAL_TYPE_ALLOCATION
    if index < len(alloc):
        return alloc[index]
    return alloc[index % len(alloc)]


def _deterministic_commercial_id(location: Dict[str, Any], index: int) -> str:
    """Stable CPROP-xxxxxxxx id derived from location + index."""
    seed = f"{location.get('name', '')}|{location.get('vertical_offset', '')}|{index}"
    h = hashlib.md5(seed.encode()).hexdigest()[:8]
    return f"CPROP-{h}"


def period_from_year(year: int) -> str:
    """Map a construction year to its PropertyPeriod menu value.

    Buckets come from the active profile (``COMMERCIAL_PERIOD_BUCKETS``): a
    list of ``(cutoff_year_exclusive, label)`` with the final cutoff ``None``.
    """
    buckets = active_profile().COMMERCIAL_PERIOD_BUCKETS
    for cutoff, label in buckets:
        if cutoff is None or year < cutoff:
            return label
    return buckets[-1][1]


def anchor_tenant(commercial_type: str) -> str:
    """Draw an anchor tenant from the per-type pool. 'Multi-let' is the
    fallback for unknown asset classes."""
    pool = active_profile().COMMERCIAL_ANCHOR_TENANT_POOL.get(
        commercial_type, ["Multi-let"])
    return random.choice(pool)


def _construction_year_for_type(commercial_type: str) -> int:
    """Draw a construction year for the given archetype.

    When the profile defines ``COMMERCIAL_CONSTRUCTION_YEAR_BANDS`` (a per-type
    list of ``((start, end), weight)``), the year is drawn from the weighted
    bands; an ``end`` of ``None`` is open-ended (current year - 1). Otherwise,
    and for types absent from the bands, a uniform draw over
    ``COMMERCIAL_CONSTRUCTION_YEAR_RANGE`` is used.
    """
    profile = active_profile()
    current_year = datetime.now().year - 1

    bands = getattr(profile, "COMMERCIAL_CONSTRUCTION_YEAR_BANDS", None)
    type_bands = bands.get(commercial_type) if bands else None
    if not type_bands:
        lo, hi = profile.COMMERCIAL_CONSTRUCTION_YEAR_RANGE
        return random.randint(lo, current_year if hi is None else hi)

    ranges = [b[0] for b in type_bands]
    weights = [b[1] for b in type_bands]
    start, end = random.choices(ranges, weights=weights, k=1)[0]
    return random.randint(start, current_year if end is None else end)


def generate_commercial_metadata(index: int, location: Dict[str, Any]) -> Dict[str, Any]:
    """Build the metadata dict for a single commercial asset.

    Output keys are a superset of property_random.generate_property_metadata
    so the shared schema walker and residential delegators read them
    transparently. ``commercial_type`` is set deterministically by index;
    area + value scale to the asset class via the per-type profile tables.
    The BRI prototype is attached only when the profile enables commercial BRI
    coding (``COMMERCIAL_BRI_ENABLED``).
    """
    profile = active_profile()
    ctype = get_commercial_type(index)
    area = round(random.uniform(*profile.COMMERCIAL_TYPE_AREA_RANGE[ctype]), 0)
    value_per_sqm = random.uniform(*profile.COMMERCIAL_TYPE_VALUE_PER_SQM[ctype])
    value_factor = location.get("value_factor", 1.0)
    value = round(area * value_per_sqm * value_factor, -3)
    construction_year = _construction_year_for_type(ctype)

    metadata = {
        "property_id": _deterministic_commercial_id(location, index),
        "commercial_type": ctype,
        # 'property_type' alias is required by residential generators that
        # look up location_info['property_type'].
        "property_type": ctype,
        "construction_year": construction_year,
        "property_area": area,
        "property_value": value,
        "elevation": location["elevation"],
        "vertical_offset": location.get("vertical_offset", 0.5),
        "area_name": location.get("name", "Unknown"),
        "value_factor": value_factor,
        "streets_data": location.get("streets_data", {}),
    }
    if profile.COMMERCIAL_BRI_ENABLED:
        metadata["bri_prototype"] = _bri_for_commercial(ctype)
    return metadata
