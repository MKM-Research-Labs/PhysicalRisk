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
