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

# src/utilities/page_01_title_overview.py

"""
Page 1: Title and Property Overview
Handles the title page with basic property information and overview.
"""

from datetime import datetime
from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from config.format import property_title_py
from .property_page_00_base import PropertyBasePage


class TitleOverviewPage(PropertyBasePage):
    """Generates the title page with property overview."""

    def generate_elements(self, property_data: Dict[str, Any],
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate title page elements."""
        elements = []

        try:
            # Extract property ID and address
            property_id = self._get_property_id(property_data)
            loc = property_data.get('PropertyHeader', {}).get('Location', {})
            prop_address = f"{loc.get('BuildingNumber', '')} {loc.get('StreetName', '')}".strip()
            prop_label = property_title_py(prop_address, property_id)

            # TITLE SECTION
            elements.append(Paragraph(
                "Comprehensive Property Analysis Report",
                self.styles['Title']
            ))
            elements.append(Paragraph(
                prop_label,
                self.styles['SubTitle']
            ))
            elements.append(Paragraph(
                f"Report Date: {datetime.now().strftime('%Y-%m-%d')}",
                self.styles['Normal']
            ))
            elements.append(Spacer(1, self.spacing['major_section']))

            # PROPERTY OVERVIEW SECTION
            elements.append(Paragraph("Property Overview", self.styles['SectionHeader']))

            header_data = property_data.get('PropertyHeader', {})
            basic_info = header_data.get('Header', {})

            # Create overview table
            overview_data = [["Property Information", "Value"]]

            # Key overview fields
            key_fields = [
                'UPRN', 'PropertyID', 'CatchmentID',
                'propertyType', 'propertyStatus',
                'DateCreated', 'LastUpdated'
            ]

            for field in key_fields:
                value = basic_info.get(field)
                if value is not None:
                    overview_data.append([
                        self._format_field_name(field),
                        self._format_value(value)
                    ])

            overview_table = Table(overview_data, colWidths=self.table_widths['two_col'])
            overview_table.setStyle(self.table_styles['standard'])
            elements.append(overview_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # PROPERTY SUMMARY SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Property Summary", self.styles['SectionHeader']))

            # Create summary from key attributes
            attributes_data = header_data.get('PropertyAttributes', {})
            summary_data = [["Key Attribute", "Value"]]

            # Key summary fields
            summary_fields = [
                ('PropertyType', 'Property Type'),
                ('PropertyAreaSqm', 'Area (sqm)'),
                ('NumberBedrooms', 'Bedrooms'),
                ('NumberBathrooms', 'Bathrooms'),
                ('PropertyCondition', 'Condition'),
                ('CouncilTaxBand', 'Council Tax Band')
            ]

            for field, label in summary_fields:
                value = attributes_data.get(field)
                if value is not None:
                    formatted_value = self._format_value(value)
                    if field == 'PropertyAreaSqm' and isinstance(value, (int, float)):
                        formatted_value = f"{value:.1f} sqm"
                    summary_data.append([label, formatted_value])

            # Add building age if available
            construction_year = attributes_data.get('ConstructionYear')
            if construction_year and isinstance(construction_year, (int, float)):
                building_age = datetime.now().year - int(construction_year)
                summary_data.append(["Building Age", f"{building_age} years"])

            summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
            summary_table.setStyle(self.table_styles['standard'])
            elements.append(summary_table)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating title and overview: {str(e)}",
                self.styles['Normal']
            ))

        return elements

    def _get_property_id(self, property_data: Dict[str, Any]) -> str:
        """Extract property ID from data."""
        try:
            return property_data['PropertyHeader']['Header']['PropertyID']
        except (KeyError, TypeError):
            return 'Unknown Property'
