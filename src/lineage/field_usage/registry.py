# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Assembled field-usage registry.

Merges the per-concern RED chains (wind, flood, fire/seismic, direct PRS) into
one exact-path lookup, and exposes the AMBER prefix rules. Pure data assembly —
no behaviour (that lives in resolve.py).
"""

from ._contract import AMBER_PREFIXES
from ._fire_seismic import FIRE_SEISMIC_FIELDS
from ._flood import FLOOD_FIELDS
from ._prs import PRS_FIELDS
from ._wind import WIND_FIELDS

# Exact CDM dotted path -> usage entry. RED entries only (AMBER is by prefix,
# GREEN is the default).
EXACT_FIELDS = {
    **WIND_FIELDS,
    **FLOOD_FIELDS,
    **FIRE_SEISMIC_FIELDS,
    **PRS_FIELDS,
}

__all__ = ["EXACT_FIELDS", "AMBER_PREFIXES"]
