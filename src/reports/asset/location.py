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

"""Render the Location section of an asset.

Four sub-tables: full primary address, geographic coordinates,
administrative areas, and area classification (density / urban-rural).
Mirrors property_page_02_location.py but as a pure section renderer.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer

from ._helpers import auto_rows, build_kv_table, section_block

# (field_key, label) for each address component
_ADDRESS_COMPONENTS = [
    ("BuildingName",       "Building Name"),
    ("BuildingNumber",     "Building Number"),
    ("SubBuildingNumber",  "Sub Building Number"),
    ("SubBuildingName",    "Sub Building Name"),
    ("StreetName",         "Street Name"),
    ("TownCity",           "Town/City"),
    ("County",             "County"),
    ("Postcode",           "Postcode"),
    ("AddressLine2",       "Address Line 2"),
]

_ADMINISTRATIVE_FIELDS = [
    ("Country",                   "Country"),
    ("Region",                    "Region"),
    ("LocalAuthority",            "Local Authority"),
    ("ElectoralWard",             "Electoral Ward"),
    ("ParliamentaryConstituency", "Parliamentary Constituency"),
]


def _build_full_address(location: Dict[str, Any]) -> str:
    parts = []
    for field in ("BuildingNumber", "StreetName", "TownCity", "County", "Postcode"):
        value = location.get(field)
        if value:
            parts.append(str(value))
    return ", ".join(parts) if parts else "Unknown"


def _classify_density(density: float) -> str:
    if density > 200:
        return "Very High Density"
    if density > 100:
        return "High Density"
    if density > 50:
        return "Medium Density"
    if density > 20:
        return "Low-Medium Density"
    return "Low Density"


def render_location(location: Dict[str, Any], page) -> List:
    """Build the four location sub-tables."""
    elements: List = [
        Paragraph("Location Details", page.styles["SectionHeader"]),
    ]

    # --- Primary Address ---
    address_rows = [("Full Address", _build_full_address(location))]
    address_rows.extend(auto_rows(location, _ADDRESS_COMPONENTS))
    elements.append(Paragraph("Primary Address", page.styles["SubSectionHeader"]))
    elements.extend(build_kv_table(
        address_rows, page, header=("Address Component", "Value")))
    elements.append(Spacer(1, page.spacing["minor_section"]))

    # --- Geographic Information ---
    lat, lon = location.get("LatitudeDegrees"), location.get("LongitudeDegrees")
    geo_rows: List = []
    if lat is not None and lon is not None:
        geo_rows.extend([
            ("Latitude",    f"{lat}°N"),
            ("Longitude",   f"{lon}°E"),
            ("Coordinates", f"{lat}°N, {lon}°E"),
        ])
    geo_rows.extend([
        ("British National Grid", location.get("BritishNationalGrid")),
        ("What3Words",            location.get("What3Words")),
        ("USRN",                  location.get("USRN")),
    ])
    geo_part = build_kv_table(geo_rows, page, header=("Geographic Detail", "Value"))
    if geo_part:
        elements.append(Paragraph("Geographic Information", page.styles["SubSectionHeader"]))
        elements.extend(geo_part)
        elements.append(Spacer(1, page.spacing["minor_section"]))

    # --- Administrative Areas ---
    admin_block = section_block(
        "Administrative Areas",
        page,
        auto_rows(location, _ADMINISTRATIVE_FIELDS),
        header=("Administrative Detail", "Value"),
    )
    elements.extend(admin_block)

    # --- Area Classification ---
    class_rows: List = []
    urban_rural = location.get("UrbanRuralClassification")
    if urban_rural:
        class_rows.append(("Urban/Rural Classification", urban_rural))
    density = location.get("LocalDensityHectare")
    if isinstance(density, (int, float)):
        class_rows.append(("Local Density", f"{density:.2f} per hectare"))
        class_rows.append(("Density Category", _classify_density(density)))
    elements.extend(section_block(
        "Area Classification", page, class_rows,
        header=("Classification", "Value"),
    ))

    return elements
