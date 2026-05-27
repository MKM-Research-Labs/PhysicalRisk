# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Render the RiskAssessment section of an asset."""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_FLOOD_FIELDS = [
    ("EAFloodZone",                 "EA Flood Zone"),
    ("OverallFloodRisk",            "Overall Flood Risk"),
    ("FloodRiskType",               "Flood Risk Type"),
    ("GroundLevelMeters",           "Ground Level (m)"),
    ("BaseFloodElevationMeters",    "Base Flood Elevation (m)"),
    ("VerticalDatum",               "Vertical Datum"),
    ("FloodDebrisPresent",          "Flood Debris Present"),
    ("GovernmentalDefenceScheme",   "Governmental Defence Scheme"),
]

_DISTANCE_FIELDS = [
    ("RiverDistanceMeters",   "River Distance (m)"),
    ("LakeDistanceMeters",    "Lake Distance (m)"),
    ("CoastalDistanceMeters", "Coastal Distance (m)"),
    ("CanalDistanceMeters",   "Canal Distance (m)"),
]

_GROUND_FIELDS = [
    ("SoilType",   "Soil Type"),
    ("SoilVs30Mps", "Soil Vs30 (m/s)"),
]


def render_risk_assessment(risk: Dict[str, Any], page) -> List:
    """Build the risk assessment tables: flood, water-distances, ground."""
    elements: List = [
        Paragraph("Risk Assessment", page.styles["SectionHeader"]),
    ]
    elements.extend(section_block(
        "Flood Risk",
        page,
        auto_rows(risk, _FLOOD_FIELDS),
        style="risk",
        header=("Flood Attribute", "Value"),
    ))
    elements.extend(section_block(
        "Distance to Water Bodies",
        page,
        auto_rows(risk, _DISTANCE_FIELDS),
        style="risk",
        header=("Water Body", "Distance"),
    ))
    elements.extend(section_block(
        "Ground Conditions",
        page,
        auto_rows(risk, _GROUND_FIELDS),
        style="risk",
        header=("Property", "Value"),
    ))
    return elements
