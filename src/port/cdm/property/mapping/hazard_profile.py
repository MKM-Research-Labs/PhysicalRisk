# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flatten ProtectionMeasures.HazardProfile (normalised hazard classes)."""


def flatten_hazard_profile(prop: dict) -> dict:
    """Return flat snake_case keys for the four hazard classes."""
    hp = prop.get("ProtectionMeasures", {}).get("HazardProfile", {})

    return {
        "flood_hazard_class":   hp.get("FloodHazardClass"),
        "wind_hazard_class":    hp.get("WindHazardClass"),
        "seismic_hazard_class": hp.get("SeismicHazardClass"),
        "fire_hazard_class":    hp.get("FireHazardClass"),
    }
