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

# src/utilities/page_13_risk_analysis.py

"""
Page 13: Comprehensive Risk Analysis
Combines property and mortgage risks for overall assessment.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from .property_page_00_base import PropertyBasePage
from .property_page_13_scoring import (
    comprehensive_risk_assessment,
    property_risk_assessment,
    identify_key_factors,
    generate_recommendations,
    generate_monitoring_schedule,
)


class RiskAnalysisPage(PropertyBasePage):
    """Generates comprehensive risk analysis page."""

    def generate_elements(self, property_data: Dict[str, Any],
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate comprehensive risk analysis page elements."""
        elements = []

        try:
            elements.append(Paragraph("Comprehensive Risk Analysis", self.styles['SectionHeader']))

            if mortgage_data:
                # Combined property and mortgage risk analysis
                risk_assessment = self._comprehensive_risk_assessment(property_data, mortgage_data)
            else:
                # Property-only risk analysis
                risk_assessment = self._property_risk_assessment(property_data)

            # OVERALL RISK SUMMARY
            elements.append(Paragraph("Overall Risk Summary", self.styles['SubSectionHeader']))

            normal = self.styles['Normal']
            summary_data = [[
                Paragraph("Risk Category", self.styles['TableHeader']),
                Paragraph("Score", self.styles['TableHeader']),
                Paragraph("Weight", self.styles['TableHeader']),
                Paragraph("Impact", self.styles['TableHeader']),
            ]]

            total_weighted_score = 0
            total_weight = 0

            for category, details in risk_assessment['categories'].items():
                score = details['score']
                weight = details['weight']
                impact = details['impact']

                total_weighted_score += score * weight
                total_weight += weight

                summary_data.append([
                    Paragraph(str(category), normal),
                    Paragraph(f"{score}/5", normal),
                    Paragraph(f"{weight}%", normal),
                    Paragraph(str(impact), normal),
                ])

            # Calculate overall score
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            overall_percentage = (overall_score / 5) * 100

            # Add summary rows (no empty separator)
            summary_data.append([
                Paragraph("OVERALL SCORE", self.styles['TableHeader']),
                Paragraph(f"{overall_score:.2f}/5.0", self.styles['TableHeader']),
                Paragraph("100%", self.styles['TableHeader']),
                Paragraph(f"{overall_percentage:.1f}%", self.styles['TableHeader']),
            ])
            summary_data.append([
                Paragraph("RISK LEVEL", self.styles['TableHeader']),
                Paragraph(str(risk_assessment['overall_level']), self.styles['TableHeader']),
                Paragraph("", normal),
                Paragraph(str(risk_assessment.get('overall_color', '')), normal),
            ])

            summary_table = Table(summary_data, colWidths=self.table_widths['risk_table'])
            summary_table.setStyle(self.table_styles['risk'])
            elements.append(summary_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # KEY RISK FACTORS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Key Risk Factors", self.styles['SubSectionHeader']))

            factors_data = [["Risk Factor", "Assessment"]]
            for factor, assessment in risk_assessment['key_factors'].items():
                factors_data.append([
                    Paragraph(str(factor), normal),
                    Paragraph(str(assessment), normal),
                ])

            factors_table = Table(factors_data, colWidths=self.table_widths['two_col'])
            factors_table.setStyle(self.table_styles['standard'])
            elements.append(factors_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # RECOMMENDATIONS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Risk Management Recommendations", self.styles['SubSectionHeader']))

            recommendations_data = [["Priority", "Recommended Action"]]
            for i, recommendation in enumerate(risk_assessment['recommendations'], 1):
                recommendations_data.append([
                    Paragraph(f"Priority {i}", normal),
                    Paragraph(str(recommendation), normal),
                ])

            recommendations_table = Table(recommendations_data, colWidths=self.table_widths['two_col'])
            recommendations_table.setStyle(self.table_styles['standard'])
            elements.append(recommendations_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # MONITORING SCHEDULE
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Recommended Monitoring Schedule", self.styles['SubSectionHeader']))

            monitoring_data = [["Monitoring Item", "Frequency"]]
            for item, frequency in risk_assessment['monitoring'].items():
                monitoring_data.append([item, frequency])

            monitoring_table = Table(monitoring_data, colWidths=self.table_widths['two_col'])
            monitoring_table.setStyle(self.table_styles['standard'])
            elements.append(monitoring_table)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating risk analysis: {str(e)}",
                self.styles['Normal']
            ))

        return elements

    def _comprehensive_risk_assessment(self, property_data: Dict[str, Any],
                                     mortgage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment with both property and mortgage data."""
        return comprehensive_risk_assessment(property_data, mortgage_data)

    def _property_risk_assessment(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform property-only risk assessment."""
        return property_risk_assessment(property_data)

    def _identify_key_factors(self, categories: Dict[str, Dict]) -> Dict[str, str]:
        """Identify the highest risk factors."""
        return identify_key_factors(categories)

    def _generate_recommendations(self, categories: Dict[str, Dict], overall_score: float) -> List[str]:
        """Generate risk management recommendations."""
        return generate_recommendations(categories, overall_score)

    def _generate_monitoring_schedule(self, overall_score: float) -> Dict[str, str]:
        """Generate appropriate monitoring schedule based on risk level."""
        return generate_monitoring_schedule(overall_score)
