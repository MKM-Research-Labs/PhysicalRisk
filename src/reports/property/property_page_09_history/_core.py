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

"""
Page 9: Property History
Handles historical flood events derived from nearest gauge daily data,
plus environmental issues and ground conditions.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from ..property_page_00_base import PropertyBasePage
from ._builders import _HistoryBuildersMixin


class HistoryPage(_HistoryBuildersMixin, PropertyBasePage):
    """Generates property history page."""

    def generate_elements(self, property_data: Dict[str, Any],
                         rloan_data: Dict[str, Any] = None) -> List:
        """Generate property history page elements."""
        elements = []

        try:
            elements.append(Paragraph("Property History", self.styles['SectionHeader']))

            history_data = property_data.get('HistoryAndIncidents', {})

            # FLOOD HISTORY — derived from nearest gauge historical daily data
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.extend(self._build_flood_history(property_data))

            # ENVIRONMENTAL ISSUES
            environmental = history_data.get('EnvironmentalIssues', {})
            if environmental:
                elements.append(Paragraph("Environmental Conditions", self.styles['SubSectionHeader']))

                env_data = [["Environmental Factor", "Status"]]
                for key, value in environmental.items():
                    if value is not None:
                        env_data.append([self._format_field_name(key), self._format_value(value)])

                env_table = Table(env_data, colWidths=self.table_widths['two_col'])
                env_table.setStyle(self.table_styles['history'])
                elements.append(env_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

            # FIRE INCIDENTS
            fire_incidents = history_data.get('FireIncidents', {})
            if fire_incidents:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Fire History", self.styles['SubSectionHeader']))

                fire_data = [["Fire Information", "Details"]]
                for key, value in fire_incidents.items():
                    if value is not None:
                        fire_data.append([self._format_field_name(key), self._format_value(value)])

                fire_table = Table(fire_data, colWidths=self.table_widths['two_col'])
                fire_table.setStyle(self.table_styles['history'])
                elements.append(fire_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

            # GROUND CONDITIONS
            ground_conditions = history_data.get('GroundConditions', {})
            if ground_conditions:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Ground Conditions", self.styles['SubSectionHeader']))

                ground_data = [["Ground Factor", "Status"]]
                for key, value in ground_conditions.items():
                    if value is not None:
                        ground_data.append([self._format_field_name(key), self._format_value(value)])

                ground_table = Table(ground_data, colWidths=self.table_widths['two_col'])
                ground_table.setStyle(self.table_styles['history'])
                elements.append(ground_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

            # HISTORICAL RISK ASSESSMENT
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Historical Risk Assessment", self.styles['SubSectionHeader']))

            risk_summary = self._assess_historical_risks(history_data)

            risk_data = [["Risk Category", "Assessment"]]
            for category, assessment in risk_summary.items():
                risk_data.append([category, assessment])

            risk_table = Table(risk_data, colWidths=self.table_widths['two_col'])
            risk_table.setStyle(self.table_styles['risk'])
            elements.append(risk_table)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating property history: {str(e)}",
                self.styles['Normal']
            ))

        return elements
