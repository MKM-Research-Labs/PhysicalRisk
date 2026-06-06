# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flood-spec compliance functions — map CDM record fields to per-measure
0-1 compliance factors and apply the spec's soft caps."""

from typing import Any, Dict, List, Optional

from .bri_constants import RESILIENCE_LEVEL_CREDIT
from .flood_constants import (
    LOWEST_FLOOR_ELEVATION_BANDS, HISTORIC_WATER_AREA_COMPLIANCE,
    LOWER_LEVEL_DESIGN_COMPLIANCE, DEFAULT_MISSING_COMPLIANCE,
)


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
