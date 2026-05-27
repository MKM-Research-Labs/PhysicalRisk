# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Render the Header section of an asset (PropertyID, UPRN, CatchmentID …)."""

from typing import Any, Dict, List

from ._helpers import auto_rows, section_block

_HEADER_FIELDS = [
    ("PropertyID",     "Property ID"),
    ("UPRN",           "UPRN"),
    ("USRN",           "USRN"),
    ("CatchmentID",    "Catchment"),
    ("propertyType",   "Property Type"),
    ("propertyStatus", "Status"),
]


def render_header(header: Dict[str, Any], page) -> List:
    """Build the header identity table from the asset's Header dict."""
    return section_block(
        "Asset Identity",
        page,
        auto_rows(header, _HEADER_FIELDS),
        style="standard",
        header=("Identifier", "Value"),
    )
