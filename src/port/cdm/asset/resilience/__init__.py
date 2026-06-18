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
