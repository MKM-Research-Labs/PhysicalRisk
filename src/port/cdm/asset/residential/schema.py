# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Residential asset schema composition.

Combines the asset-common schema dicts (asset.header, asset.resilience,
asset.energy, asset.history) with residential-specific extensions
(asset.residential.contents) into the same nested shape the legacy
property pipeline emits, so generated property.json stays structurally
identical.
"""

from ..energy import ENERGY_PERFORMANCE_SCHEMA
from ..header import HEADER_SCHEMA
from ..history import HISTORY_AND_INCIDENTS_SCHEMA, TRANSACTION_HISTORY_SCHEMA
from ..resilience import (
    HAZARD_PROFILE_SCHEMA,
    RATINGS_SCHEMA,
    RESILIENCE_MEASURES_SCHEMA,
    RISK_ASSESSMENT_SCHEMA,
)
from .contents import CONTENTS_SCHEMA

# Default elevation when GroundLevelMeters is absent (prevents unrealistic
# flood calculations).
DEFAULT_ELEVATION: float = 12.0

PROPERTY_SCHEMA = {
    "PropertyHeader": {
        **HEADER_SCHEMA,
        "RiskAssessment": RISK_ASSESSMENT_SCHEMA,
        "Contents": CONTENTS_SCHEMA,
    },
    "ProtectionMeasures": {
        "RiskAssessment": RATINGS_SCHEMA,
        "HazardProfile": HAZARD_PROFILE_SCHEMA,
        "ResilienceMeasures": RESILIENCE_MEASURES_SCHEMA,
    },
    "EnergyPerformance": ENERGY_PERFORMANCE_SCHEMA,
    "HistoryAndIncidents": HISTORY_AND_INCIDENTS_SCHEMA,
    "TransactionHistory": TRANSACTION_HISTORY_SCHEMA,
}
