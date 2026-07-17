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

"""Commercial-only: CommercialAttributes section."""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from reports.asset._helpers import auto_rows, section_block

from ..base import CommercialBasePage

_CLASSIFICATION_FIELDS = [
    ("CommercialType",        "Commercial Type"),
    ("UseClassUKO",           "Use Class (UKO)"),
    ("BusinessRatesCategory", "Business Rates Category"),
    ("OccupancyStatus",       "Occupancy Status"),
    ("PropertyCondition",     "Property Condition"),
]

_AREA_FIELDS = [
    ("PropertyAreaSqm",     "Gross Property Area (sqm)"),
    ("NetInternalAreaSqm",  "Net Internal Area (sqm)"),
    ("NetLettableAreaSqm",  "Net Lettable Area (sqm)"),
    ("NumberOfStoreys",     "Number of Storeys"),
    ("TotalUnits",          "Total Units"),
    ("ParkingSpaces",       "Parking Spaces"),
    ("LoadingBays",         "Loading Bays"),
]

_BUILDING_INFRA_FIELDS = [
    ("ConstructionYear",     "Construction Year"),
    ("PropertyPeriod",       "Property Period"),
    ("PlantRoomLocation",    "Plant Room Location"),
    ("ServiceCore",          "Service Core"),
    ("LastMajorWorksDate",   "Last Major Works"),
]


class CommercialAttributesPage(CommercialBasePage):
    """Builds the CommercialAttributes page (commercial-only section)."""

    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        attrs = (commercial_data.get("CommercialAsset", {}) or {}).get(
            "CommercialAttributes", {}
        ) or {}

        elements: List = [
            Paragraph("Commercial Attributes", self.styles["SectionHeader"]),
        ]
        elements.extend(section_block(
            "Classification",
            self,
            auto_rows(attrs, _CLASSIFICATION_FIELDS),
            header=("Attribute", "Value"),
        ))
        elements.extend(section_block(
            "Area & Units",
            self,
            auto_rows(attrs, _AREA_FIELDS),
            header=("Metric", "Value"),
        ))
        elements.extend(section_block(
            "Building Infrastructure",
            self,
            auto_rows(attrs, _BUILDING_INFRA_FIELDS),
            header=("Attribute", "Value"),
        ))
        return elements
