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

"""Commercial-only: Tenancy section (covenant, WAULT, yields)."""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from reports.asset._helpers import auto_rows, section_block

from ..base import CommercialBasePage

_TENANT_FIELDS = [
    ("AnchorTenant",     "Anchor Tenant"),
    ("CovenantStrength", "Covenant Strength"),
    ("WAULT",            "WAULT (years)"),
]

_YIELD_FIELDS = [
    ("ServiceChargeGbpPerSqm", "Service Charge (per sqm)"),
    ("NetInitialYield",        "Net Initial Yield"),
    ("EquivalentYield",        "Equivalent Yield"),
    ("ReversionaryYield",      "Reversionary Yield"),
]


class TenancyPage(CommercialBasePage):
    """Builds the Tenancy page."""

    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        tenancy = (commercial_data.get("CommercialAsset", {}) or {}).get(
            "Tenancy", {}
        ) or {}

        elements: List = [
            Paragraph("Tenancy & Yields", self.styles["SectionHeader"]),
        ]
        elements.extend(section_block(
            "Anchor & Covenant",
            self,
            auto_rows(tenancy, _TENANT_FIELDS),
            style="tenancy",
            header=("Field", "Value"),
        ))
        elements.extend(section_block(
            "Yields & Charges",
            self,
            auto_rows(tenancy, _YIELD_FIELDS),
            style="tenancy",
            header=("Metric", "Value"),
        ))
        return elements
