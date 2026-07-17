# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
