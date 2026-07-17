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

"""
Page 7: Protection Measures
Handles flood protection, resilience measures, and risk mitigation systems.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from ..property_page_00_base import PropertyBasePage
from ._sections_a import _SectionsAMixin
from ._sections_b import _SectionsBMixin

__all__ = ["ProtectionPage"]


class ProtectionPage(_SectionsAMixin, _SectionsBMixin, PropertyBasePage):
    """Generates protection measures page."""

    def generate_elements(self, property_data: Dict[str, Any],
                          rloan_data: Dict[str, Any] = None) -> List:
        """Generate protection measures page elements."""
        elements = []

        try:
            elements.append(Paragraph("Protection Measures", self.styles['SectionHeader']))

            protection_data = property_data.get('ProtectionMeasures', {})

            if not protection_data:
                elements.append(Paragraph("No protection measures data available.", self.styles['Normal']))
                return elements

            self._add_hazard_profile(elements, protection_data)
            self._add_risk_assessment(elements, protection_data)
            self._add_resilience_measures(elements, protection_data)
            self._add_natural_measures(elements, protection_data)
            self._add_recommendations(elements, protection_data)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating protection measures: {str(e)}",
                self.styles['Normal']
            ))

        return elements
