# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
