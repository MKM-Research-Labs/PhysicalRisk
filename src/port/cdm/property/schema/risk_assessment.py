# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
PropertyHeader.RiskAssessment — hazard and exposure facts about the property.

Covers §1.6 of the revised Property CDM. Assessment outcomes and ratings live in
schema/ratings.py; normalised hazard classes live in schema/hazard_profile.py.
"""

RISK_ASSESSMENT_SCHEMA = {
    "EAFloodZone": {
        "type": "menu",
        "options": ["Zone 1", "Zone 2", "Zone 3a", "Zone 3b"],
        "description": "Environment Agency flood zone"
    },
    "OverallFloodRisk": {
        "type": "menu",
        "options": ["Very low", "Low", "Medium", "High", "Very high"],
        "description": "Overall flood risk assessment"
    },
    "FloodRiskType": {
        "type": "menu",
        "options": ["Fluvial", "Pluvial", "GroundWater", "Coastal", "Multiple"],
        "description": "Primary type of flood risk (drives flood-resilience regime)"
    },
    "GroundLevelMeters": {
        "type": "decimal",
        "description": "Height above sea level in meters"
    },
    "RiverDistanceMeters": {
        "type": "decimal",
        "description": "Distance to nearest river in meters"
    },
    "LastFloodDate": {
        "type": "date",
        "description": "Date of most recent flood event at this property"
    },
    "SoilType": {
        "type": "menu",
        "options": [
            "Clay", "Sandy", "Loamy", "Chalk", "Peat", "Rocky", "Mixed",
            "Saltpans", "Unknown",
        ],
        "description": "Predominant soil composition"
    },
    "LakeDistanceMeters": {
        "type": "decimal",
        "description": "Distance to nearest lake in meters"
    },
    "CoastalDistanceMeters": {
        "type": "decimal",
        "description": "Distance to coastline in meters"
    },
    "CanalDistanceMeters": {
        "type": "decimal",
        "description": "Distance to nearest canal in meters"
    },
    "GovernmentalDefenceScheme": {
        "type": "boolean",
        "description": "Covered by government flood defence scheme"
    }
}
