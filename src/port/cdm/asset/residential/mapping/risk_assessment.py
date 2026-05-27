# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flatten PropertyHeader.RiskAssessment (hazard/exposure facts)."""


def flatten_risk_assessment(prop: dict, default_elevation: float) -> dict:
    """Return flat snake_case keys for PropertyHeader.RiskAssessment.

    GroundLevelMeters falls back to ``default_elevation`` when absent; the
    ``elevation`` alias mirrors the same value for flood-model compatibility.
    """
    risk = prop.get("PropertyHeader", {}).get("RiskAssessment", {})

    ground_level = risk.get("GroundLevelMeters")
    if ground_level is None:
        ground_level = default_elevation

    return {
        "flood_zone":          risk.get("EAFloodZone"),
        "overall_flood_risk":  risk.get("OverallFloodRisk"),
        "flood_risk_type":     risk.get("FloodRiskType"),
        "ground_level_meters": ground_level,
        "elevation":           ground_level,
        "river_distance":      risk.get("RiverDistanceMeters"),
        "base_flood_elevation_m": risk.get("BaseFloodElevationMeters"),
        "vertical_datum":          risk.get("VerticalDatum"),
        "soil_vs30_mps":           risk.get("SoilVs30Mps"),
        "flood_debris_present":    risk.get("FloodDebrisPresent"),
    }
