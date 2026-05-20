# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
ProtectionMeasures.HazardProfile — normalised hazard classes per peril.

Covers §2.2 of the revised Property CDM. These are derived categorical
attributes consumed by downstream resilience scoring; they are not raw hazard
facts (which live in schema/risk_assessment.py) but standardised classes used
across utilities so the same building scores consistently across frameworks.
"""

_HAZARD_CLASS_OPTIONS = ["None", "Low", "Medium", "High", "Extreme"]

HAZARD_PROFILE_SCHEMA = {
    "FloodHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised flood hazard class for the site"
    },
    "WindHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised wind/storm hazard class for the site"
    },
    "SeismicHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised seismic hazard class for the site"
    },
    "FireHazardClass": {
        "type": "menu",
        "options": _HAZARD_CLASS_OPTIONS,
        "description": "Normalised fire/wildfire hazard class for the site"
    },
    "DesignWindSpeedKmh": {
        "type": "decimal",
        "description": "Site design wind speed in km/h corresponding to WindHazardClass"
    },
    "DesignFloodReturnYr": {
        "type": "integer",
        "description": "Design flood return period in years (e.g. 100 = 1-in-100yr)"
    },
    "DesignSeismicPGA": {
        "type": "decimal",
        "description": "Peak ground acceleration in g for mapped seismic hazard class"
    },
}
