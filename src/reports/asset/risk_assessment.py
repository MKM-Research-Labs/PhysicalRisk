# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
