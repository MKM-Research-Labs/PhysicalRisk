# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Render the ProtectionMeasures section.

CDM sub-shape:
    ProtectionMeasures
      RiskAssessment
        InsuranceBodyRatings { … }
        GoverningBodyRatings { … }
      HazardProfile          { FloodHazardClass, WindHazardClass, … }
      ResilienceMeasures
        BuildingAssessment   (may be empty)
        SiteAndDrainage      (may be empty)
        FloodProtection      { FloodGates, FloodBarriers, … }
        FireProtection       (may be empty)
        ContinuityMeasures   (may be empty)
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_INSURANCE_FIELDS = [
    ("InsuranceRating",        "Insurance Rating"),
    ("InsuranceDate",          "Insurance Date"),
    ("InsuranceRatingVersion", "Insurance Rating Version"),
    ("InsuranceRatingBody",    "Insurance Rating Body"),
]

_GOVERNING_FIELDS = [
    ("BRIDate",          "BRI Date"),
    ("BRIRatingVersion", "BRI Rating Version"),
    ("BRIRatingAgent",   "BRI Rating Agent"),
]

_HAZARD_FIELDS = [
    ("FloodHazardClass",      "Flood Hazard Class"),
    ("WindHazardClass",       "Wind Hazard Class"),
    ("SeismicHazardClass",    "Seismic Hazard Class"),
    ("FireHazardClass",       "Fire Hazard Class"),
    ("DesignWindSpeedKmh",    "Design Wind Speed (km/h)"),
    ("DesignFloodReturnYr",   "Design Flood Return Period (yr)"),
    ("DesignSeismicPGA",      "Design Seismic PGA"),
]

_FLOOD_PROTECTION_FIELDS = [
    ("FloodGates",         "Flood Gates"),
    ("FloodBarriers",      "Flood Barriers"),
    ("SumpPump",           "Sump Pump"),
    ("FloodWarningSystem", "Flood Warning System"),
]


def render_protection(protection: Dict[str, Any], page) -> List:
    """Build the protection measures tables."""
    elements: List = [
        Paragraph("Protection Measures", page.styles["SectionHeader"]),
    ]

    risk = protection.get("RiskAssessment", {}) or {}
    elements.extend(section_block(
        "Insurance Body Ratings",
        page,
        auto_rows(risk.get("InsuranceBodyRatings", {}) or {}, _INSURANCE_FIELDS),
        style="protection",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "Governing Body Ratings",
        page,
        auto_rows(risk.get("GoverningBodyRatings", {}) or {}, _GOVERNING_FIELDS),
        style="protection",
        header=("Field", "Value"),
    ))

    elements.extend(section_block(
        "Hazard Profile",
        page,
        auto_rows(protection.get("HazardProfile", {}) or {}, _HAZARD_FIELDS),
        style="protection",
        header=("Hazard", "Value"),
    ))

    resilience = protection.get("ResilienceMeasures", {}) or {}
    elements.extend(section_block(
        "Flood Protection Measures",
        page,
        auto_rows(resilience.get("FloodProtection", {}) or {}, _FLOOD_PROTECTION_FIELDS),
        style="protection",
        header=("Measure", "Status"),
    ))
    return elements
