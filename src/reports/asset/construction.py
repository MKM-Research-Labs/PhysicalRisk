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

"""Render the Construction section of an asset (incl. nested RoofDetails)."""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_CONSTRUCTION_FIELDS = [
    ("ConstructionType",   "Construction Type"),
    ("FoundationType",     "Foundation Type"),
    ("FloorType",          "Floor Type"),
    ("FloorLevelMeters",   "Floor Level (m)"),
    ("PropertyHeight",     "Property Height (m)"),
    ("BasementPresent",    "Basement"),
    ("StiltsHeight",       "Stilts Height (m)"),
    ("RetrofitYear",       "Retrofit Year"),
    ("BrickVeneer",        "Brick Veneer"),
    ("GlassType",          "Glass Type"),
    ("SoftStory",          "Soft Story"),
    ("ShapeIrregularity",  "Shape Irregularity"),
    ("HasCrippleWall",     "Cripple Wall"),
]

_ROOF_FIELDS = [
    ("RoofCover",        "Roof Cover"),
    ("RoofGeometry",     "Roof Geometry"),
    ("RoofPitch",        "Roof Pitch"),
    ("RoofFrame",        "Roof Frame"),
    ("RoofDeck",         "Roof Deck"),
    ("RoofYearReplaced", "Roof Year Replaced"),
]


def render_construction(construction: Dict[str, Any], page) -> List:
    """Build the construction tables (main + roof sub-table)."""
    elements: List = [
        Paragraph("Construction Details", page.styles["SectionHeader"]),
    ]
    elements.extend(section_block(
        "Building Structure",
        page,
        auto_rows(construction, _CONSTRUCTION_FIELDS),
        header=("Attribute", "Value"),
    ))

    roof = construction.get("RoofDetails") or {}
    if roof:
        elements.extend(section_block(
            "Roof Details",
            page,
            auto_rows(roof, _ROOF_FIELDS),
            header=("Roof Attribute", "Value"),
        ))
    return elements
