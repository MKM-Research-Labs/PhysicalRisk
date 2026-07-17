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

"""Shared commercial asset random value generators.

One implementation for every catchment. Commercial-specific menus and per-type
sizing read from the active catchment profile; shared fields delegate to
``property_random``:

    metadata.py    — id / type / area / value sizing per index
    generators.py  — commercial-only field generators + dispatcher

Per-catchment archetype tables live in ``port.rand.profiles.<catchment>``. For
backward compatibility the historical constant names (``TYPE_AREA_RANGE`` …)
remain importable from this package and resolve, at access time, to the active
profile's tables (see ``__getattr__``).
"""

from .generators import generate_field_value  # noqa: F401
from .metadata import (  # noqa: F401
    anchor_tenant,
    generate_commercial_metadata,
    get_commercial_type,
    period_from_year,
)

# Convenience: parity with property_random's generate_property_metadata
# (build_section calls this name via the shared schema walker).
generate_property_metadata = generate_commercial_metadata


# Legacy constant name -> active-profile attribute. Kept so existing callers /
# tests can still do ``from ...commercial_random import TYPE_AREA_RANGE`` and
# get the active catchment's table without forking a per-catchment constants
# module.
_LEGACY_CONSTANTS = {
    "ANCHOR_TENANT_POOL": "COMMERCIAL_ANCHOR_TENANT_POOL",
    "COMMERCIAL_TYPE_ALLOCATION": "COMMERCIAL_TYPE_ALLOCATION",
    "COMMERCIAL_CONSTRUCTION_TYPES": "COMMERCIAL_CONSTRUCTION_TYPES",
    "TYPE_AREA_RANGE": "COMMERCIAL_TYPE_AREA_RANGE",
    "TYPE_VALUE_PER_SQM": "COMMERCIAL_TYPE_VALUE_PER_SQM",
    "TYPE_USE_CLASS": "COMMERCIAL_TYPE_USE_CLASS",
    "TYPE_BUSINESS_RATES": "COMMERCIAL_TYPE_BUSINESS_RATES",
    "TYPE_STOREYS": "COMMERCIAL_TYPE_STOREYS",
    "TYPE_TOTAL_UNITS": "COMMERCIAL_TYPE_TOTAL_UNITS",
    "TYPE_PARKING_SPACES": "COMMERCIAL_TYPE_PARKING_SPACES",
    "TYPE_LOADING_BAYS": "COMMERCIAL_TYPE_LOADING_BAYS",
}


def __getattr__(name: str):
    """PEP 562: resolve legacy constant names from the active profile."""
    profile_attr = _LEGACY_CONSTANTS.get(name)
    if profile_attr is not None:
        from port.rand.profiles import active_profile
        return getattr(active_profile(), profile_attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "anchor_tenant",
    "generate_commercial_metadata",
    "generate_field_value",
    "generate_property_metadata",
    "get_commercial_type",
    "period_from_year",
]
