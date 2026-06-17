# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Field-usage downstream lineage for CDM fields.

Classifies each CDM field by how far downstream its value travels — RED (feeds
PRS pricing), AMBER (contract / operational) or GREEN (report only) — and
returns the lineage chain to the consuming model / output. See resolve.py for
the public functions.
"""

from .registry import AMBER_PREFIXES, EXACT_FIELDS
from .resolve import classify, lineage, tier_meta
from .tiers import AMBER, DEFAULT_TIER, GREEN, RED, TIER_META

__all__ = [
    "classify",
    "lineage",
    "tier_meta",
    "RED",
    "AMBER",
    "GREEN",
    "DEFAULT_TIER",
    "TIER_META",
    "EXACT_FIELDS",
    "AMBER_PREFIXES",
]
