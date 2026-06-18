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

"""Resilience generator constants — period/condition/zone priors used to
synthesise plausible checklists, plus section-field membership."""

from typing import Dict, List

# Single authoritative definitions live in config (parameter governance).
from config.bri import (
    RESILIENCE_DEFAULT_PERIOD_PROB as _DEFAULT_PERIOD_PROB,
    RESILIENCE_DEFAULT_CONDITION_MULT as _DEFAULT_CONDITION_MULT,
)


# "Baseline probability that any one resilience boolean is True" for each
# construction period. Captures the qualitative consensus that 1890s
# Victorians are over-engineered survivors while 1960s-70s stock cuts corners.
_PERIOD_BASE_PROB: Dict[str, float] = {
    "Pre-1919":     0.40,
    "1919-1944":    0.35,
    "1945-1975":    0.25,
    "1976-1999":    0.40,
    "2000-2008":    0.55,
    "2009-Present": 0.70,
}

_CONDITION_MULTIPLIER: Dict[str, float] = {
    "Excellent": 1.35,
    "Good":      1.10,
    "Fair":      1.00,
    "Poor":      0.70,
    "Very poor": 0.40,
}

# Fields that didn't exist as concepts in older buildings — heavily damped
# for pre-1976 stock regardless of condition.
_MODERN_ONLY_FIELDS: set = {
    "FloodWarningSystem",
    "AutomaticDetectionInstalled",
    "SuppressionSystemsInstalled",
    "BackflowPreventionInstalled",
    "CriticalITProtected",
    "TelecomRedundancyProvided",
    "BackupPowerInstalled",
    "BackupPowerProtectedFromHazard",
    "DeployableBarriersProvided",
}

_FLOOD_PROTECTION_FIELDS: set = {
    "FloodGates", "FloodBarriers", "SumpPump", "FloodWarningSystem",
    "PermanentFloodProofingAtEntries", "DeployableBarriersProvided",
    "BackflowPreventionInstalled", "FinishedFloorAboveDesignFlood",
    "ElectricalSystemsAboveFlood", "MechanicalSystemsAboveFlood",
    "FuelAndHazardousStoresProtected", "OccupiedLevelsElevated",
    "OnsiteDrainageSizedForDesignStorm",
}

_FLOOD_ZONE_UPLIFT: Dict[str, float] = {
    "Zone 1":  0.00,
    "Zone 2":  0.10,
    "Zone 3a": 0.25,
    "Zone 3b": 0.40,
}

_ALWAYS_LIKELY_TRUE: set = {
    "SiteFloodHazardAssessed",
    "SiteExposureAssessed",
    "SiteGeotechnicalAssessed",
}

# Field membership in each sub-section. Mirror of the CDM resilience modules.
SECTION_FIELDS: Dict[str, List[str]] = {
    "BuildingAssessment": [
        "SiteExposureAssessed", "OrientationMitigatesWind",
        "StructureDesignedForHazardWind", "ContinuousLoadPathProvided",
        "LateralBracingAdequate", "RoofRatedForDesignWind",
        "RoofEdgeDetailWindResistant", "CladdingRatedForDesignWind",
        "OpeningsWindResistant", "LargeDoorsReinforced",
        "RooftopEquipmentAnchored", "FacadeAttachmentsAnchored",
        "StructuralFireResistanceAdequate", "CompartmentsProvided",
        "FireStoppingAtPenetrations", "ExternalMaterialsFireResistant",
        "SiteGeotechnicalAssessed", "StructureMeetsSeismicCode",
        "SeismicDetailingToStandard", "StructuralRegularityAdequate",
        "FoundationSuitableForHazard", "NonstructuralComponentsAnchored",
        "HeavyEquipmentAnchored",
    ],
    "SiteAndDrainage": [
        "SiteFloodHazardAssessed", "HighRiskZoneAvoidedOrJustified",
        "FinishedFloorAboveDesignFlood", "OccupiedLevelsElevated",
        # BasementFloodStrategy handled separately (enum)
        "OnsiteDrainageSizedForDesignStorm", "OverlandFlowPathsMaintained",
        "PermeableOrRetentionMeasures", "WildfireDefensibleSpace",
        "WildfireNonCombustiblePerimeter", "HighRiskGroundAvoidedOrMitigated",
        "LiquefactionMitigationProvided",
    ],
    "FloodProtection": [
        "PermanentFloodProofingAtEntries", "DeployableBarriersProvided",
        "BackflowPreventionInstalled", "ElectricalSystemsAboveFlood",
        "MechanicalSystemsAboveFlood", "FuelAndHazardousStoresProtected",
        "FloodGates", "FloodBarriers", "SumpPump", "FloodWarningSystem",
    ],
    "FireProtection": [
        "AutomaticDetectionInstalled", "SuppressionSystemsInstalled",
    ],
    "ContinuityMeasures": [
        "BackupPowerInstalled", "BackupPowerProtectedFromHazard",
        "BackupWaterSupplyProvided", "WaterSystemsProtectedFromHazard",
        "TelecomRedundancyProvided", "CriticalITProtected",
        "AccessRouteResilient", "AccessDesignConsidersHazards",
        "BusinessContinuityPlanInPlace", "EmergencyProceduresTested",
    ],
}

# Mirrors schema/resilience.py:RESILIENCE_LEVELS.
_RESILIENCE_LEVELS = ["Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified"]
