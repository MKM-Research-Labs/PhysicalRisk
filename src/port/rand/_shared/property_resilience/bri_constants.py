# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""BRI letter-rating constants — section/field weights, level credits,
rating thresholds, and per-hazard relevance maps."""

from typing import Dict


# Resilience sub-section weights (must sum to 1.0).
# Thames calibration: flood-heavy, wind/seismic/fire deprioritised.
SECTION_WEIGHTS: Dict[str, float] = {
    "FloodProtection":     0.30,
    "SiteAndDrainage":     0.25,
    "BuildingAssessment":  0.20,
    "ContinuityMeasures":  0.15,
    "FireProtection":      0.10,
}

# Per-field overrides within each sub-section. Unlisted fields default to 1.0.
FIELD_WEIGHTS: Dict[str, Dict[str, float]] = {
    "BuildingAssessment": {
        "StructureDesignedForHazardWind":    2.0,
        "ContinuousLoadPathProvided":        2.0,
        "StructureMeetsSeismicCode":         2.0,
        "FoundationSuitableForHazard":       1.5,
        "StructuralFireResistanceAdequate":  1.5,
        "LateralBracingAdequate":            1.5,
    },
    "SiteAndDrainage": {
        "FinishedFloorAboveDesignFlood":      2.0,
        "OccupiedLevelsElevated":             1.5,
        "HighRiskZoneAvoidedOrJustified":     1.5,
        "OnsiteDrainageSizedForDesignStorm":  1.5,
        "SiteFloodHazardAssessed":            1.5,
    },
    "FloodProtection": {
        "PermanentFloodProofingAtEntries":    2.0,
        "ElectricalSystemsAboveFlood":        2.0,
        "MechanicalSystemsAboveFlood":        2.0,
        "DeployableBarriersProvided":         1.5,
        "BackflowPreventionInstalled":        1.5,
        "FuelAndHazardousStoresProtected":    1.5,
    },
    "ContinuityMeasures": {
        "BackupPowerInstalled":              1.5,
        "BackupPowerProtectedFromHazard":    1.5,
        "AccessRouteResilient":              1.5,
        "BusinessContinuityPlanInPlace":     1.0,
        "EmergencyProceduresTested":         1.0,
    },
    "FireProtection": {
        "AutomaticDetectionInstalled":  1.0,
        "SuppressionSystemsInstalled":  1.0,
    },
}

# Resilience checklist 5-level enum → credit fraction.
# Mirrors the menu options in schema/resilience.py:RESILIENCE_LEVELS.
RESILIENCE_LEVEL_CREDIT: Dict[str, float] = {
    "Not assessed":  0.0,
    "Partial":       0.4,
    "Meets minimum": 0.7,
    "Enhanced":      0.9,
    "Verified":      1.0,
}

# BasementFloodStrategy is its own enum (strategy choice, not assessment level).
BASEMENT_FLOOD_STRATEGY_CREDIT: Dict[str, float] = {
    "No basement":                            1.0,
    "Flood-resistant basement":               1.0,
    "Deliberately floodable with protection": 0.75,
    "None":                                   0.0,
}

# Lower-bound score for each rating. Below "B" → NR.
# Calibrated against the Thames synthetic property generator to hit the
# TARGET_DISTRIBUTION_THAMES mix of 10/20/40/30.
RATING_THRESHOLDS: Dict[str, float] = {
    "AA": 0.87,
    "A":  0.62,
    "B":  0.38,
}

RATING_ORDER: tuple = ("AA", "A", "B", "NR")

# Per-hazard relevance: which resilience fields drive each hazard's sub-rating.
HAZARD_RELEVANT_FIELDS: Dict[str, list] = {
    "Flood": [
        "PermanentFloodProofingAtEntries", "DeployableBarriersProvided",
        "BackflowPreventionInstalled", "ElectricalSystemsAboveFlood",
        "MechanicalSystemsAboveFlood", "FuelAndHazardousStoresProtected",
        "FloodGates", "FloodBarriers", "SumpPump", "FloodWarningSystem",
        "SiteFloodHazardAssessed", "HighRiskZoneAvoidedOrJustified",
        "FinishedFloorAboveDesignFlood", "OccupiedLevelsElevated",
        "BasementFloodStrategy", "OnsiteDrainageSizedForDesignStorm",
        "OverlandFlowPathsMaintained", "PermeableOrRetentionMeasures",
    ],
    "Wind": [
        "SiteExposureAssessed", "OrientationMitigatesWind",
        "StructureDesignedForHazardWind", "ContinuousLoadPathProvided",
        "LateralBracingAdequate", "RoofRatedForDesignWind",
        "RoofEdgeDetailWindResistant", "CladdingRatedForDesignWind",
        "OpeningsWindResistant", "LargeDoorsReinforced",
        "RooftopEquipmentAnchored", "FacadeAttachmentsAnchored",
        "StructuralRegularityAdequate",
    ],
    "Fire": [
        "StructuralFireResistanceAdequate", "CompartmentsProvided",
        "FireStoppingAtPenetrations", "ExternalMaterialsFireResistant",
        "WildfireDefensibleSpace", "WildfireNonCombustiblePerimeter",
        "AutomaticDetectionInstalled", "SuppressionSystemsInstalled",
    ],
    "Seismic": [
        "SiteGeotechnicalAssessed", "StructureMeetsSeismicCode",
        "SeismicDetailingToStandard", "StructuralRegularityAdequate",
        "FoundationSuitableForHazard", "NonstructuralComponentsAnchored",
        "HeavyEquipmentAnchored", "LateralBracingAdequate",
        "HighRiskGroundAvoidedOrMitigated", "LiquefactionMitigationProvided",
    ],
}

# Continuity-section score required to award the "+" modifier on the overall.
CONTINUITY_PLUS_THRESHOLD: float = 0.65

# Calibration target for the Thames synthetic property population.
TARGET_DISTRIBUTION_THAMES: Dict[str, float] = {
    "AA": 0.10,
    "A":  0.20,
    "B":  0.40,
    "NR": 0.30,
}
