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
