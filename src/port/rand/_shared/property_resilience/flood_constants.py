# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flood-spec model constants (per BRI Resilience Function Specification) —
13-measure weights, regime multipliers, compliance maps, soft caps, alpha."""

from typing import Dict, List, Tuple


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
