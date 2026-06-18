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

"""Commercial-only: AccessibilityFeatures section."""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from reports.asset._helpers import auto_rows, section_block

from ..base import CommercialBasePage

_ACCESSIBILITY_FIELDS = [
    ("DisabledAccess",       "Disabled Access"),
    ("GoodsLiftCount",       "Goods Lifts"),
    ("GoodsLiftCapacityKg",  "Goods Lift Capacity (kg)"),
    ("EmergencyExits",       "Emergency Exits"),
    ("DeliveryBays",         "Delivery Bays"),
]


class AccessibilityPage(CommercialBasePage):
    """Builds the AccessibilityFeatures page."""

    def generate_elements(self, commercial_data: Dict[str, Any], **kwargs) -> List:
        access = (commercial_data.get("CommercialAsset", {}) or {}).get(
            "AccessibilityFeatures", {}
        ) or {}

        elements: List = [
            Paragraph("Accessibility & Loading Features",
                      self.styles["SectionHeader"]),
        ]
        elements.extend(section_block(
            "Building Access",
            self,
            auto_rows(access, _ACCESSIBILITY_FIELDS),
            style="accessibility",
            header=("Feature", "Value"),
        ))
        return elements
