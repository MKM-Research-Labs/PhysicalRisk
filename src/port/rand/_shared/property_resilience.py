# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Property resilience — catchment-shared single source of truth.

This module is the consolidated home for everything resilience-related for the
synthetic property pipeline. The calibration here (section/field weights,
thresholds, period/condition/zone priors, flood-spec weights) is identical
across catchments, so every catchment's
``property/property_random/resilience.py`` is a thin shim that delegates here.

It contains, in order:

  1. BRI letter-rating CONSTANTS    — section/field weights, level credits,
                                      rating thresholds, hazard relevance.
  2. BRI letter-rating FUNCTIONS    — score_section, score_hazard,
                                      compute_bri_rating, calibration helpers.
  3. Resilience GENERATOR CONSTANTS — period/condition/zone priors used to
                                      synthesise plausible checklists.
  4. Resilience GENERATOR FUNCTIONS — generate_resilience, sanity check.
  5. Flood-spec MODEL CONSTANTS     — 13-measure weights, regime multipliers,
                                      compliance maps, soft caps, alpha.
  6. Flood-spec MODEL FUNCTIONS     — compute_compliance, regime score,
                                      damage modifier, apply_flood_resilience_score.

The two per-catchment toggles — ``PUBLISH_BRI_LETTER_RATINGS`` (whether the
catchment publishes certified BRI letter grades) and ``BRI_SCORES_ENABLED``
(whether the five numeric BRIScore fields are computed) — are deliberately NOT
defined here. They live in each catchment's shim module, which forwards its
local BRI flag into ``apply_flood_resilience_score`` via ``bri_scores_enabled``.
"""

import random
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ============================================================================
# 1. BRI letter-rating constants
# ============================================================================

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


# ============================================================================
# 2. BRI letter-rating functions
# ============================================================================

def _field_credit(field: str, value: Any) -> float:
    """Return 0.0-1.0 credit for a single checklist value.

    Recognised value types:
      - 5-level resilience enum string ("Not assessed".."Verified")
      - BasementFloodStrategy enum (different vocabulary)
      - Legacy boolean (still credited 1.0 / 0.0 for back-compat)
    """
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if field == "BasementFloodStrategy":
        return BASEMENT_FLOOD_STRATEGY_CREDIT.get(value, 0.0)
    if value in RESILIENCE_LEVEL_CREDIT:
        return RESILIENCE_LEVEL_CREDIT[value]
    return 0.0


def score_section(section_name: str, section_data: Dict[str, Any]) -> float:
    """Weighted points-achieved / points-possible for one resilience sub-section."""
    if not section_data:
        return 0.0
    field_weights = FIELD_WEIGHTS.get(section_name, {})
    possible = 0.0
    achieved = 0.0
    for field, value in section_data.items():
        w = field_weights.get(field, 1.0)
        possible += w
        achieved += w * _field_credit(field, value)
    return achieved / possible if possible else 0.0


def _map_score_to_rating(score: float) -> str:
    if score >= RATING_THRESHOLDS["AA"]:
        return "AA"
    if score >= RATING_THRESHOLDS["A"]:
        return "A"
    if score >= RATING_THRESHOLDS["B"]:
        return "B"
    return "NR"


def _flatten_resilience(resilience: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten the nested resilience dict to {field_name: value} for hazard scoring."""
    flat: Dict[str, Any] = {}
    for sub in resilience.values():
        if isinstance(sub, dict):
            flat.update(sub)
    return flat


def score_hazard(hazard: str, resilience: Dict[str, Any]) -> float:
    """Weighted 0-1 score for the resilience fields relevant to one hazard."""
    fields = HAZARD_RELEVANT_FIELDS.get(hazard, [])
    if not fields:
        return 0.0
    flat = _flatten_resilience(resilience)
    all_field_weights: Dict[str, float] = {}
    for section_weights in FIELD_WEIGHTS.values():
        all_field_weights.update(section_weights)
    possible = 0.0
    achieved = 0.0
    for field in fields:
        w = all_field_weights.get(field, 1.0)
        possible += w
        achieved += w * _field_credit(field, flat.get(field))
    return achieved / possible if possible else 0.0


def compute_bri_rating(
    resilience_measures: Dict[str, Any],
    hazard_profile: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Aggregate a property's resilience checklist into a BRI rating.

    Returns ``{rating, score, section_scores, hazard_ratings, hazard_scores}``.
    Overall letter is the weakest of the applicable hazard sub-ratings
    (HazardClass == "None" makes a hazard non-applicable). A "+" suffix is
    appended when continuity is strong and overall is not NR.
    """
    section_scores: Dict[str, float] = {}
    weighted_total = 0.0
    weight_used = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        s = score_section(section, resilience_measures.get(section, {}))
        section_scores[section] = s
        weighted_total += weight * s
        weight_used += weight
    overall_score = weighted_total / weight_used if weight_used else 0.0

    hazard_profile = hazard_profile or {}
    hazard_ratings: Dict[str, str] = {}
    hazard_scores: Dict[str, Any] = {}
    applicable_letters: list = []
    for hazard in ("Flood", "Wind", "Fire", "Seismic"):
        hazard_class = hazard_profile.get(f"{hazard}HazardClass")
        if hazard_class == "None":
            hazard_ratings[hazard] = "N/A"
            hazard_scores[hazard] = None
            continue
        s = score_hazard(hazard, resilience_measures)
        hazard_scores[hazard] = round(s, 4)
        letter = _map_score_to_rating(s)
        hazard_ratings[hazard] = letter
        applicable_letters.append(letter)

    if applicable_letters:
        worst_idx = max(RATING_ORDER.index(l) for l in applicable_letters)
        overall_letter = RATING_ORDER[worst_idx]
    else:
        overall_letter = _map_score_to_rating(overall_score)

    if (
        overall_letter != "NR"
        and section_scores.get("ContinuityMeasures", 0.0) >= CONTINUITY_PLUS_THRESHOLD
    ):
        overall_letter = overall_letter + "+"

    return {
        "rating": overall_letter,
        "score": round(overall_score, 4),
        "section_scores": {k: round(v, 4) for k, v in section_scores.items()},
        "hazard_ratings": hazard_ratings,
        "hazard_scores": hazard_scores,
    }


def distribution_summary(
    ratings: Iterable[str],
    target: Dict[str, float] = None,
) -> Dict[str, Dict[str, float]]:
    """Compare actual rating distribution vs. target. Returns per-rating
    {actual, target, delta} dict."""
    target = target or TARGET_DISTRIBUTION_THAMES
    ratings = list(ratings)
    total = len(ratings) or 1
    counts = {r: 0 for r in RATING_ORDER}
    for r in ratings:
        if r in counts:
            counts[r] += 1
    return {
        r: {
            "actual": counts[r] / total,
            "target": target.get(r, 0.0),
            "delta":  counts[r] / total - target.get(r, 0.0),
        }
        for r in RATING_ORDER
    }


def recalibrate_thresholds_from_scores(
    scores: List[float],
    target: Dict[str, float] = None,
) -> Dict[str, float]:
    """Derive score thresholds that reproduce the target distribution."""
    target = target or TARGET_DISTRIBUTION_THAMES
    if not scores:
        return dict(RATING_THRESHOLDS)
    ranked = sorted(scores, reverse=True)
    n = len(ranked)
    aa_idx = max(0, int(round(target["AA"] * n)) - 1)
    a_idx = max(0, int(round((target["AA"] + target["A"]) * n)) - 1)
    b_idx = max(0, int(round((target["AA"] + target["A"] + target["B"]) * n)) - 1)
    return {"AA": ranked[aa_idx], "A": ranked[a_idx], "B": ranked[b_idx]}


def validate_weights(section_weights: Optional[Dict[str, float]] = None) -> None:
    """Raise ``ValueError`` if the section weights do not sum to 1.0.

    ``section_weights`` lets a catchment shim pass its own (possibly
    monkeypatched) ``SECTION_WEIGHTS`` so the check observes that module's
    rebound value; defaults to this module's ``SECTION_WEIGHTS``.
    """
    weights = SECTION_WEIGHTS if section_weights is None else section_weights
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"SECTION_WEIGHTS sum to {total:.6f}, expected 1.0. "
            f"Adjust weights in resilience.py."
        )


# ============================================================================
# 3. Resilience generator constants (age/condition/zone priors)
# ============================================================================

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
_DEFAULT_PERIOD_PROB = 0.40

_CONDITION_MULTIPLIER: Dict[str, float] = {
    "Excellent": 1.35,
    "Good":      1.10,
    "Fair":      1.00,
    "Poor":      0.70,
    "Very poor": 0.40,
}
_DEFAULT_CONDITION_MULT = 1.0

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


# ============================================================================
# 4. Resilience generator functions
# ============================================================================

def _level_from_score(score: float) -> str:
    """Map a 0-1 propensity score to one of the 5 resilience levels.

    Bucket boundaries: 0-0.2 Not assessed, 0.2-0.4 Partial, 0.4-0.6 Meets minimum,
    0.6-0.8 Enhanced, 0.8-1.0 Verified.
    """
    if score < 0.20: return "Not assessed"
    if score < 0.40: return "Partial"
    if score < 0.60: return "Meets minimum"
    if score < 0.80: return "Enhanced"
    return "Verified"


def _field_probability(
    field: str,
    base: float,
    cond_mult: float,
    flood_uplift: float,
    is_modern_period: bool,
) -> float:
    """Per-field True-probability after applying period/condition/zone modifiers."""
    p = base * cond_mult
    if field in _FLOOD_PROTECTION_FIELDS:
        p += flood_uplift
    if field in _MODERN_ONLY_FIELDS and not is_modern_period:
        p *= 0.20
    if field in _ALWAYS_LIKELY_TRUE:
        p = max(p, 0.75)
    return max(0.02, min(0.95, p))


def _basement_strategy(
    basement_present: bool,
    period: str,
    cond_mult: float,
    rng: random.Random,
) -> str:
    """Pick BasementFloodStrategy consistent with whether a basement exists."""
    if not basement_present:
        return "No basement"
    is_modern = period in {"2000-2008", "2009-Present"}
    if is_modern and rng.random() < 0.6 * cond_mult:
        return rng.choices(
            ["Flood-resistant basement", "Deliberately floodable with protection"],
            weights=[0.7, 0.3],
        )[0]
    return "None"


def _extract_metadata(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the fields the resilience generator needs out of a built property record."""
    ph = property_data.get("PropertyHeader", {})
    attrs = ph.get("PropertyAttributes", {})
    construction = ph.get("Construction", {})
    risk = ph.get("RiskAssessment", {})
    return {
        "period":           attrs.get("PropertyPeriod", "1976-1999"),
        "condition":        attrs.get("PropertyCondition", "Fair"),
        "flood_zone":       risk.get("EAFloodZone", "Zone 1"),
        "basement_present": bool(construction.get("BasementPresent", False)),
    }


def generate_resilience(
    property_data: Dict[str, Any],
    rng: Optional[random.Random] = None,
) -> Dict[str, Dict[str, Any]]:
    """Build the ``ProtectionMeasures.ResilienceMeasures`` dict for one property."""
    rng = rng or random
    meta = _extract_metadata(property_data)
    period = meta["period"]
    is_modern_period = period in {"1976-1999", "2000-2008", "2009-Present"}
    base = _PERIOD_BASE_PROB.get(period, _DEFAULT_PERIOD_PROB)
    cond_mult = _CONDITION_MULTIPLIER.get(meta["condition"], _DEFAULT_CONDITION_MULT)
    flood_uplift = _FLOOD_ZONE_UPLIFT.get(meta["flood_zone"], 0.0)

    resilience: Dict[str, Dict[str, Any]] = {}
    for section, fields in SECTION_FIELDS.items():
        section_data: Dict[str, Any] = {}
        for field in fields:
            p = _field_probability(field, base, cond_mult, flood_uplift, is_modern_period)
            score = max(0.0, min(1.0, p + rng.uniform(-0.20, 0.20)))
            section_data[field] = _level_from_score(score)
        resilience[section] = section_data

    resilience["SiteAndDrainage"]["BasementFloodStrategy"] = _basement_strategy(
        meta["basement_present"], period, cond_mult,
        rng if isinstance(rng, random.Random) else random.Random(),
    )

    return resilience


# Sanity-check distribution helpers ------------------------------------------

# Plausible Thames-stock distribution by construction period.
_PERIOD_WEIGHTS: List[tuple] = [
    ("Pre-1919",     0.18),
    ("1919-1944",    0.16),
    ("1945-1975",    0.24),
    ("1976-1999",    0.20),
    ("2000-2008",    0.12),
    ("2009-Present", 0.10),
]

_CONDITION_WEIGHTS: List[tuple] = [
    ("Excellent", 0.10), ("Good", 0.35), ("Fair", 0.35),
    ("Poor", 0.15), ("Very poor", 0.05),
]

_FLOOD_ZONE_WEIGHTS: List[tuple] = [
    ("Zone 1", 0.55), ("Zone 2", 0.25), ("Zone 3a", 0.15), ("Zone 3b", 0.05),
]


def _weighted_choice(weights: List[tuple], rng: random.Random) -> str:
    options, ws = zip(*weights)
    return rng.choices(options, weights=ws)[0]


def _synthetic_property(rng: random.Random) -> Dict[str, Any]:
    return {
        "PropertyHeader": {
            "PropertyAttributes": {
                "PropertyPeriod":    _weighted_choice(_PERIOD_WEIGHTS, rng),
                "PropertyCondition": _weighted_choice(_CONDITION_WEIGHTS, rng),
            },
            "Construction": {"BasementPresent": rng.random() < 0.25},
            "RiskAssessment": {"EAFloodZone": _weighted_choice(_FLOOD_ZONE_WEIGHTS, rng)},
        }
    }


def sanity_check_distribution(sample_size: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """Generate ``sample_size`` synthetic Thames properties, score them, and
    report the BRI rating distribution alongside the Thames target."""
    rng = random.Random(seed)
    ratings: List[str] = []
    scores: List[float] = []
    examples: List[Dict[str, Any]] = []
    for i in range(sample_size):
        prop = _synthetic_property(rng)
        prop["ProtectionMeasures"] = {"ResilienceMeasures": generate_resilience(prop, rng)}
        result = compute_bri_rating(prop["ProtectionMeasures"]["ResilienceMeasures"])
        ratings.append(result["rating"])
        scores.append(result["score"])
        if i < 3:
            attrs = prop["PropertyHeader"]["PropertyAttributes"]
            examples.append({
                "period":    attrs["PropertyPeriod"],
                "condition": attrs["PropertyCondition"],
                "zone":      prop["PropertyHeader"]["RiskAssessment"]["EAFloodZone"],
                "rating":    result["rating"],
                "score":     result["score"],
            })

    return {
        "sample_size": sample_size,
        "distribution": distribution_summary(ratings),
        "mean_score": round(sum(scores) / len(scores), 4),
        "examples": examples,
    }


# ============================================================================
# 5. Flood-spec model constants (per BRI Resilience Function Specification)
# ============================================================================

# Spec base weights — 13 measures, sum to 100.
FLOOD_SPEC_BASE_WEIGHTS: Dict[str, int] = {
    "lowest_occupied_floor_elevation":    20,
    "critical_systems_elevation":         15,
    "site_drainage_topography":           10,
    "onsite_retainage_capacity":          10,
    "permeable_surface_share":             6,
    "backflow_protection":                 6,
    "lower_level_flood_compatible_design": 8,
    "water_resistant_materials":           8,
    "debris_impact_resistance":            5,
    "roof_drainage_standard":              4,
    "roof_membrane_openings_seal":         3,
    "sump_pumps_backup_power":             3,
    "historic_water_area_flag":            2,
}

# Regime-specific weight multipliers from the spec.
FLOOD_SPEC_REGIME_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "pluvial": {
        "lowest_occupied_floor_elevation":    1.0,
        "critical_systems_elevation":         1.0,
        "site_drainage_topography":           1.3,
        "onsite_retainage_capacity":          1.3,
        "permeable_surface_share":            1.3,
        "backflow_protection":                1.2,
        "lower_level_flood_compatible_design": 0.9,
        "water_resistant_materials":          0.9,
        "debris_impact_resistance":           0.8,
        "roof_drainage_standard":             1.1,
        "roof_membrane_openings_seal":        1.0,
        "sump_pumps_backup_power":            1.2,
        "historic_water_area_flag":           1.0,
    },
    "fluvial": {
        "lowest_occupied_floor_elevation":    1.2,
        "critical_systems_elevation":         1.1,
        "site_drainage_topography":           0.9,
        "onsite_retainage_capacity":          0.9,
        "permeable_surface_share":            0.8,
        "backflow_protection":                1.0,
        "lower_level_flood_compatible_design": 1.2,
        "water_resistant_materials":          1.1,
        "debris_impact_resistance":           1.0,
        "roof_drainage_standard":             0.9,
        "roof_membrane_openings_seal":        1.0,
        "sump_pumps_backup_power":            1.0,
        "historic_water_area_flag":           1.0,
    },
    "coastal": {
        "lowest_occupied_floor_elevation":    1.2,
        "critical_systems_elevation":         1.1,
        "site_drainage_topography":           0.8,
        "onsite_retainage_capacity":          0.8,
        "permeable_surface_share":            0.7,
        "backflow_protection":                0.9,
        "lower_level_flood_compatible_design": 1.2,
        "water_resistant_materials":          1.1,
        "debris_impact_resistance":           1.2,
        "roof_drainage_standard":             0.9,
        "roof_membrane_openings_seal":        1.0,
        "sump_pumps_backup_power":            0.9,
        "historic_water_area_flag":           1.0,
    },
}

# Spec elevation-margin → compliance table for lowest_occupied_floor_elevation.
LOWEST_FLOOR_ELEVATION_BANDS: List[Tuple[float, float]] = [
    (0.0, 0.00),   # < 0 m
    (1.0, 0.20),   # 0–1 m
    (3.0, 0.50),   # 1–3 m
    (5.0, 0.75),   # 3–5 m
    (6.0, 0.90),   # 5–6 m
    (float("inf"), 1.00),  # 6+ m
]

# FloodDamageSeverity → compliance for historic_water_area_flag.
# Higher severity → more adverse history → lower compliance.
HISTORIC_WATER_AREA_COMPLIANCE: Dict[str, float] = {
    "No damage":          1.0,
    "Minor damage":       0.75,
    "Moderate damage":    0.5,
    "Significant damage": 0.25,
    "Severe damage":      0.0,
}

# BasementFloodStrategy → compliance for lower_level_flood_compatible_design.
LOWER_LEVEL_DESIGN_COMPLIANCE: Dict[str, float] = {
    "No basement":                            1.0,
    "Flood-resistant basement":               1.0,
    "Deliberately floodable with protection": 0.75,
    "None":                                   0.0,
}

# Soft caps (Section 5 of the spec).
# Each cap is a (condition_fn, cap_value) tuple evaluated against the
# compliance dict + regime.
FLOOD_SPEC_SOFT_CAPS = [
    ("lowest_occupied_floor_elevation_zero", 40.0),
    ("critical_systems_elevation_zero",      60.0),
    ("pluvial_retainage_and_drainage_zero",  55.0),
    ("fluvcoast_lower_level_and_materials_zero", 65.0),
]

# Damage modifier α by regime.
FLOOD_SPEC_ALPHA_BY_REGIME: Dict[str, float] = {
    "pluvial": 0.65,
    "fluvial": 0.60,
    "coastal": 0.50,
}

# Map CDM FloodRiskType (post D3 rename) → spec regime keys.
REGIME_FROM_FLOOD_RISK_TYPE: Dict[str, str] = {
    "Fluvial":    "fluvial",
    "Pluvial":    "pluvial",
    "GroundWater": "pluvial",  # groundwater behaves like surface/pluvial
    "Coastal":    "coastal",
    "Multiple":   "pluvial",   # worst α — most conservative
}

# Default regime when FloodRiskType is missing.
DEFAULT_REGIME = "fluvial"

# Default compliance for missing values (spec recommends 0.25 + confidence penalty).
DEFAULT_MISSING_COMPLIANCE = 0.25


# ============================================================================
# 6. Flood-spec model functions
# ============================================================================

def _elevation_to_compliance(meters: Optional[float]) -> float:
    """Map a floor elevation in metres to a 0-1 compliance factor."""
    if meters is None:
        return DEFAULT_MISSING_COMPLIANCE
    try:
        m = float(meters)
    except (TypeError, ValueError):
        return DEFAULT_MISSING_COMPLIANCE
    for upper, compliance in LOWEST_FLOOR_ELEVATION_BANDS:
        if m < upper:
            return compliance
    return 1.0


def _ordinal_5level_compliance(value: Optional[str]) -> float:
    """Map our 5-level RESILIENCE_LEVELS enum to a 0-1 compliance factor."""
    if value is None:
        return DEFAULT_MISSING_COMPLIANCE
    return RESILIENCE_LEVEL_CREDIT.get(value, DEFAULT_MISSING_COMPLIANCE)


def _get(record: Dict, path: List[str], default=None):
    cur = record
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p, default)
    return cur


def compute_compliance(measure_code: str, property_record: Dict[str, Any]) -> float:
    """Return the 0-1 compliance factor for one spec measure, reading inputs
    from the CDM record per the D2 mapping."""
    R = property_record  # alias

    if measure_code == "lowest_occupied_floor_elevation":
        return _elevation_to_compliance(
            _get(R, ["PropertyHeader", "Construction", "FloorLevelMeters"])
        )

    if measure_code == "critical_systems_elevation":
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "FloodProtection",
            "ElectricalSystemsAboveFlood",
        ]))

    if measure_code == "site_drainage_topography":
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "SiteAndDrainage",
            "OverlandFlowPathsMaintained",
        ]))

    if measure_code == "onsite_retainage_capacity":
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "SiteAndDrainage",
            "OnsiteDrainageSizedForDesignStorm",
        ]))

    if measure_code == "permeable_surface_share":
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "SiteAndDrainage",
            "PermeableOrRetentionMeasures",
        ]))

    if measure_code == "backflow_protection":
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "FloodProtection",
            "BackflowPreventionInstalled",
        ]))

    if measure_code == "lower_level_flood_compatible_design":
        strategy = _get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "SiteAndDrainage",
            "BasementFloodStrategy",
        ])
        if strategy is None:
            return DEFAULT_MISSING_COMPLIANCE
        return LOWER_LEVEL_DESIGN_COMPLIANCE.get(strategy, DEFAULT_MISSING_COMPLIANCE)

    if measure_code == "water_resistant_materials":
        # Proxy: PermanentFloodProofingAtEntries (closest 5-level resilience field).
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "FloodProtection",
            "PermanentFloodProofingAtEntries",
        ]))

    if measure_code == "debris_impact_resistance":
        # Proxy: wind-rated openings.
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "BuildingAssessment",
            "OpeningsWindResistant",
        ]))

    if measure_code == "roof_drainage_standard":
        # Proxy: wind-rated roof — same underlying engineering quality.
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "BuildingAssessment",
            "RoofRatedForDesignWind",
        ]))

    if measure_code == "roof_membrane_openings_seal":
        return _ordinal_5level_compliance(_get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "BuildingAssessment",
            "RoofEdgeDetailWindResistant",
        ]))

    if measure_code == "sump_pumps_backup_power":
        sump = _get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "FloodProtection", "SumpPump",
        ])
        backup = _get(R, [
            "ProtectionMeasures", "ResilienceMeasures", "ContinuityMeasures",
            "BackupPowerInstalled",
        ])
        return min(_ordinal_5level_compliance(sump), _ordinal_5level_compliance(backup))

    if measure_code == "historic_water_area_flag":
        severity = _get(R, [
            "HistoryAndIncidents", "FloodEvents", "FloodDamageSeverity",
        ])
        if severity is None:
            return 1.0  # no recorded flood event → clear
        return HISTORIC_WATER_AREA_COMPLIANCE.get(severity, DEFAULT_MISSING_COMPLIANCE)

    raise KeyError(f"Unknown flood-spec measure code: {measure_code}")


def _apply_soft_caps(s_raw: float, compliance: Dict[str, float], regime: str) -> float:
    """Apply spec soft caps. Returns min of s_raw and all triggered caps."""
    caps: List[float] = [100.0]
    if compliance.get("lowest_occupied_floor_elevation", 1.0) == 0.0:
        caps.append(40.0)
    if compliance.get("critical_systems_elevation", 1.0) == 0.0:
        caps.append(60.0)
    if (
        regime == "pluvial"
        and compliance.get("onsite_retainage_capacity", 1.0) == 0.0
        and compliance.get("site_drainage_topography", 1.0) == 0.0
    ):
        caps.append(55.0)
    if (
        regime in {"fluvial", "coastal"}
        and compliance.get("lower_level_flood_compatible_design", 1.0) == 0.0
        and compliance.get("water_resistant_materials", 1.0) == 0.0
    ):
        caps.append(65.0)
    return max(1.0, min(s_raw, min(caps)))


def compute_flood_resilience_score(
    property_record: Dict[str, Any],
    regime: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute the spec's flood resilience score for a property.

    Args:
        property_record: Full nested property CDM record.
        regime: Override the regime; if omitted, derived from
            ``PropertyHeader.RiskAssessment.FloodRiskType``.

    Returns:
        ``{
            "score_raw":   float,  # 0-100, pre-cap
            "score_final": float,  # 1-100, post-cap, regime-adjusted
            "regime":      str,
            "compliance":  {measure_code: float},
        }``
    """
    if regime is None:
        flood_type = _get(property_record, [
            "PropertyHeader", "RiskAssessment", "FloodRiskType",
        ])
        regime = REGIME_FROM_FLOOD_RISK_TYPE.get(flood_type, DEFAULT_REGIME)
    if regime not in FLOOD_SPEC_REGIME_MULTIPLIERS:
        regime = DEFAULT_REGIME

    compliance: Dict[str, float] = {}
    weighted_sum = 0.0
    weight_total = 0.0
    multipliers = FLOOD_SPEC_REGIME_MULTIPLIERS[regime]
    for code, base_w in FLOOD_SPEC_BASE_WEIGHTS.items():
        c = compute_compliance(code, property_record)
        compliance[code] = round(c, 4)
        w = base_w * multipliers[code]
        weighted_sum += w * c
        weight_total += w

    s_raw = 100.0 * weighted_sum / weight_total if weight_total else 0.0
    s_raw = max(0.0, min(100.0, s_raw))
    s_final = _apply_soft_caps(s_raw, compliance, regime)

    return {
        "score_raw":   round(s_raw, 4),
        "score_final": round(s_final, 4),
        "regime":      regime,
        "compliance":  compliance,
    }


def damage_modifier(score_final: float, regime: str) -> float:
    """M(S, r) = 1 - α_r × (S - 1) / 99. Returns 1.0 at S=1, (1-α) at S=100."""
    alpha = FLOOD_SPEC_ALPHA_BY_REGIME.get(regime, FLOOD_SPEC_ALPHA_BY_REGIME["fluvial"])
    return round(1.0 - alpha * ((score_final - 1.0) / 99.0), 4)


def apply_flood_resilience_score(
    property_record: Dict[str, Any],
    jitter_band: float = 0.05,
    *,
    bri_scores_enabled: bool = True,
) -> Dict[str, Any]:
    """Compute the flood resilience score for the property and write the
    five BRI score fields into ``GoverningBodyRatings``.

    Storage convention: scores are persisted on the 0-1 scale (matching the
    schema's BRIFloodScore description). The spec's 1-100 ``score_final`` is
    divided by 100 before storage. Non-flood hazard scores are jittered copies
    of the flood score within ±``jitter_band`` on the 0-1 scale (default ±0.05
    = ±5 on the spec's 1-100 scale, per the design directive).

    The overall BRIScore is the mean of the four per-hazard scores.

    ``bri_scores_enabled`` is forwarded by the catchment shim from its local
    ``BRI_SCORES_ENABLED`` flag. When False, the five numeric BRIScore fields
    are stamped 0.0 and no BRI-driven floor uplift is applied (the catchment
    does not own a certified BRI regime).

    Returns the full model output dict (raw, final, regime, compliance,
    modifier) for inspection.
    """
    result = compute_flood_resilience_score(property_record)
    modifier = damage_modifier(result["score_final"], result["regime"])

    flood_score = round(result["score_final"] / 100.0, 4)

    pm = property_record.setdefault("ProtectionMeasures", {})
    ra = pm.setdefault("RiskAssessment", {})
    gbr = ra.setdefault("GoverningBodyRatings", {})

    if not bri_scores_enabled:
        # Catchment disables numeric BRI: stamp every score 0.0 and apply no
        # BRI-driven floor uplift (flood filter falls back to raw floor level).
        for field in ("BRIFloodScore", "BRIWindScore", "BRIFireScore",
                      "BRISeismicScore", "BRIScore"):
            gbr[field] = 0.0
        return {
            **result,
            "damage_modifier": modifier,
        }

    # Property-keyed RNG so jitter is deterministic for a given property ID.
    property_id = _get(property_record, ["PropertyHeader", "Header", "PropertyID"], "X")
    rng = random.Random(hash(property_id) % (2**32))

    gbr["BRIFloodScore"] = flood_score
    for hazard in ("Wind", "Fire", "Seismic"):
        score = max(0.01, min(1.0, flood_score + rng.uniform(-jitter_band, jitter_band)))
        gbr[f"BRI{hazard}Score"] = round(score, 4)

    gbr["BRIScore"] = round(
        (gbr["BRIFloodScore"] + gbr["BRIWindScore"]
         + gbr["BRIFireScore"] + gbr["BRISeismicScore"]) / 4.0,
        4,
    )

    # Stamp the BRI-adjusted flood-threshold floor level into Construction.
    # A resilient building only counts as flooded once water rises above this
    # raised floor; the PRS flood filter reads this field. Computed from the
    # 0-1 BRIFloodScore just written above. If the surveyed FloorLevelMeters is
    # missing, leave the field unset — the flood code falls back to deriving it
    # from BRIFloodScore at evaluation time.
    from models.floodrisk.depth_damage import bri_adjusted_floor_level
    construction = property_record.setdefault("PropertyHeader", {}).setdefault(
        "Construction", {})
    floor_level = construction.get("FloorLevelMeters")
    if floor_level is not None:
        try:
            construction["BRIAdjustedFloorLevelMeters"] = round(
                bri_adjusted_floor_level(float(floor_level), flood_score), 2)
        except (TypeError, ValueError):
            pass

    return {
        **result,
        "damage_modifier": modifier,
    }
