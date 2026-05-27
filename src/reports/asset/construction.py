# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
