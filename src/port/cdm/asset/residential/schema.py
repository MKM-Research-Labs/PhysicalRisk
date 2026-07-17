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
