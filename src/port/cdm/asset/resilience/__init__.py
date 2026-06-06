# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)
"""
Asset resilience schema — hazard exposure, hazard profile, resilience checklist, ratings.

Holds four schema dicts as separate module-level names so the legacy
composition in property/schema/__init__.py continues to resolve to the
same PROPERTY_SCHEMA shape:

    RISK_ASSESSMENT_SCHEMA      raw hazard exposure facts
    HAZARD_PROFILE_SCHEMA       normalised hazard classes
    RATINGS_SCHEMA              insurance + governing-body (BRI) ratings
    RESILIENCE_MEASURES_SCHEMA  5 sub-section resilience checklist

The 5-level RESILIENCE_LEVELS vocabulary is exported for downstream BRI
scoring code that needs to compare option lists against the canonical set.
"""

from port.cdm.asset.resilience._exposure import (
    HAZARD_PROFILE_SCHEMA,
    RISK_ASSESSMENT_SCHEMA,
    _HAZARD_CLASS_OPTIONS,
)
from port.cdm.asset.resilience._ratings import RATINGS_SCHEMA
from port.cdm.asset.resilience._checklist import (
    BUILDING_ASSESSMENT_SCHEMA,
    CONTINUITY_MEASURES_SCHEMA,
    FIRE_PROTECTION_SCHEMA,
    FLOOD_PROTECTION_SCHEMA,
    RESILIENCE_LEVELS,
    RESILIENCE_MEASURES_SCHEMA,
    SITE_AND_DRAINAGE_SCHEMA,
)

__all__ = [
    "RISK_ASSESSMENT_SCHEMA",
    "HAZARD_PROFILE_SCHEMA",
    "RATINGS_SCHEMA",
    "RESILIENCE_LEVELS",
    "RESILIENCE_MEASURES_SCHEMA",
    "BUILDING_ASSESSMENT_SCHEMA",
    "SITE_AND_DRAINAGE_SCHEMA",
    "FLOOD_PROTECTION_SCHEMA",
    "FIRE_PROTECTION_SCHEMA",
    "CONTINUITY_MEASURES_SCHEMA",
]
