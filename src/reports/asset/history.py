# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Render the HistoryAndIncidents section.

Sub-shape:
    HistoryAndIncidents
      EnvironmentalIssues  { AirQuality, WaterQuality, NoisePollution, LastEnvironmentalIssueDate }
      FireIncidents        { FireDamageSeverity }
      FloodEvents          { FloodReturnPeriod, FloodDamageSeverity }
      GroundConditions     { SubsidenceStatus, ContaminationStatus, GroundStability }
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_ENV_FIELDS = [
    ("AirQuality",                  "Air Quality"),
    ("WaterQuality",                "Water Quality"),
    ("NoisePollution",              "Noise Pollution"),
    ("LastEnvironmentalIssueDate",  "Last Environmental Issue"),
]

_FIRE_FIELDS = [
    ("FireDamageSeverity", "Fire Damage Severity"),
]

_FLOOD_FIELDS = [
    ("FloodReturnPeriod",   "Flood Return Period (years)"),
    ("FloodDamageSeverity", "Flood Damage Severity"),
]

_GROUND_FIELDS = [
    ("SubsidenceStatus",     "Subsidence Status"),
    ("ContaminationStatus",  "Contamination Status"),
    ("GroundStability",      "Ground Stability"),
]


def render_history(history: Dict[str, Any], page) -> List:
    """Build the history and incidents tables."""
    elements: List = [
        Paragraph("History & Incidents", page.styles["SectionHeader"]),
    ]
    elements.extend(section_block(
        "Environmental Issues",
        page,
        auto_rows(history.get("EnvironmentalIssues", {}) or {}, _ENV_FIELDS),
        style="history",
        header=("Issue", "Value"),
    ))
    elements.extend(section_block(
        "Fire Incidents",
        page,
        auto_rows(history.get("FireIncidents", {}) or {}, _FIRE_FIELDS),
        style="history",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "Flood Events",
        page,
        auto_rows(history.get("FloodEvents", {}) or {}, _FLOOD_FIELDS),
        style="history",
        header=("Field", "Value"),
    ))
    elements.extend(section_block(
        "Ground Conditions",
        page,
        auto_rows(history.get("GroundConditions", {}) or {}, _GROUND_FIELDS),
        style="history",
        header=("Field", "Value"),
    ))
    return elements
