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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# src/utilities/page_07_protection.py

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
