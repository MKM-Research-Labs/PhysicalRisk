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
Page 15: Data Summary & Report Metadata
Handles data completeness analysis and report generation metadata.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from ..property_page_00_base import PropertyBasePage
from ._analysis import _DataAnalysisMixin


class DataSummaryPage(_DataAnalysisMixin, PropertyBasePage):
    """Generates data summary and report metadata page."""

    def generate_elements(self, property_data: Dict[str, Any],
                         rloan_data: Dict[str, Any] = None) -> List:
        """Generate data summary page elements."""
        elements = []

        try:
            elements.append(Paragraph("Data Summary & Report Metadata", self.styles['SectionHeader']))

            # DATA COMPLETENESS ANALYSIS
            elements.append(Paragraph("Data Completeness Analysis", self.styles['SubSectionHeader']))

            completeness_stats = self._analyze_data_completeness(property_data, rloan_data)

            completeness_data = [["Data Section", "Fields Used", "Total Available", "Completeness"]]

            total_used = 0
            total_available = 0

            for section, stats in completeness_stats.items():
                used = stats['used']
                available = stats['available']
                percentage = stats['percentage']

                total_used += used
                total_available += available

                completeness_data.append([
                    section,
                    str(used),
                    str(available),
                    f"{percentage:.1f}%"
                ])

            # Overall totals
            overall_percentage = (total_used / total_available * 100) if total_available > 0 else 0
            completeness_data.append(["", "", "", ""])
            completeness_data.append([
                "OVERALL TOTAL",
                str(total_used),
                str(total_available),
                f"{overall_percentage:.1f}%"
            ])

            completeness_table = Table(completeness_data, colWidths=self.table_widths['four_col'])
            completeness_table.setStyle(self.table_styles['standard'])
            elements.append(completeness_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # DATA QUALITY ASSESSMENT
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Data Quality Assessment", self.styles['SubSectionHeader']))

            quality_assessment = self._assess_data_quality(overall_percentage, completeness_stats)

            quality_data = [["Quality Metric", "Assessment"]]
            for metric, assessment in quality_assessment.items():
                quality_data.append([metric, assessment])

            quality_table = Table(quality_data, colWidths=self.table_widths['two_col'])
            quality_table.setStyle(self.table_styles['standard'])
            elements.append(quality_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # REPORT GENERATION METADATA
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Report Generation Metadata", self.styles['SubSectionHeader']))

            metadata = self._generate_report_metadata(property_data, rloan_data)

            metadata_data = [["Metadata Item", "Value"]]
            for item, value in metadata.items():
                metadata_data.append([item, value])

            metadata_table = Table(metadata_data, colWidths=self.table_widths['two_col'])
            metadata_table.setStyle(self.table_styles['standard'])
            elements.append(metadata_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # RECOMMENDATIONS FOR DATA IMPROVEMENT
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Data Improvement Recommendations", self.styles['SubSectionHeader']))

            recommendations = self._generate_data_recommendations(completeness_stats)

            if recommendations:
                rec_data = [["Priority", "Recommendation"]]
                for i, recommendation in enumerate(recommendations, 1):
                    rec_data.append([f"Priority {i}", recommendation])

                rec_table = Table(rec_data, colWidths=self.table_widths['two_col'])
                rec_table.setStyle(self.table_styles['standard'])
                elements.append(rec_table)
            else:
                elements.append(Paragraph("No specific data improvement recommendations at this time.", self.styles['Normal']))

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating data summary: {str(e)}",
                self.styles['Normal']
            ))

        return elements
