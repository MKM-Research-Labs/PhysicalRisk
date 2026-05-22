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

from .property_page_00_base import PropertyBasePage


class ProtectionPage(PropertyBasePage):
    """Generates protection measures page."""

    def generate_elements(self, property_data: Dict[str, Any],
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate protection measures page elements."""
        elements = []

        try:
            elements.append(Paragraph("Protection Measures", self.styles['SectionHeader']))

            protection_data = property_data.get('ProtectionMeasures', {})

            if not protection_data:
                elements.append(Paragraph("No protection measures data available.", self.styles['Normal']))
                return elements

            # HAZARD PROFILE
            hazard_profile = protection_data.get('HazardProfile', {})
            if hazard_profile:
                elements.append(Paragraph("Hazard Profile", self.styles['SubSectionHeader']))

                _CLASS_COLOUR = {
                    'None': '—', 'Low': 'Low', 'Medium': 'Moderate',
                    'High': 'High', 'Extreme': 'EXTREME',
                }
                hazard_data = [["Hazard", "Class", "Design Intensity"]]
                for hazard, label in [
                    ('Flood',   'Flood'),
                    ('Wind',    'Wind'),
                    ('Seismic', 'Seismic'),
                    ('Fire',    'Fire / Wildfire'),
                ]:
                    cls = hazard_profile.get(f'{hazard}HazardClass', '—')
                    cls_label = _CLASS_COLOUR.get(cls, cls)

                    if hazard == 'Flood':
                        rp = hazard_profile.get('DesignFloodReturnYr')
                        intensity = f"1-in-{rp} yr" if rp else '—'
                    elif hazard == 'Wind':
                        ws = hazard_profile.get('DesignWindSpeedKmh')
                        intensity = f"{ws:.0f} km/h" if isinstance(ws, (int, float)) else '—'
                    elif hazard == 'Seismic':
                        pga = hazard_profile.get('DesignSeismicPGA')
                        intensity = f"{pga:.3f} g" if isinstance(pga, (int, float)) else '—'
                    else:
                        intensity = '—'

                    hazard_data.append([label, cls_label, intensity])

                hazard_table = Table(hazard_data, colWidths=[
                    self.table_widths['two_col'][0] * 0.5,
                    self.table_widths['two_col'][0] * 0.5,
                    self.table_widths['two_col'][1],
                ])
                hazard_table.setStyle(self.table_styles['standard'])
                elements.append(hazard_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

            # INSURANCE & RISK ASSESSMENT
            risk_assessment = protection_data.get('RiskAssessment', {})
            if risk_assessment:
                elements.append(Paragraph("Insurance & Risk Assessment", self.styles['SubSectionHeader']))

                # Insurance Body Ratings
                ins_ratings = risk_assessment.get('InsuranceBodyRatings', {})
                if ins_ratings:
                    ins_data = [["Insurance Rating", "Details"]]
                    ins_data.append(["Rating Body", ins_ratings.get('InsuranceRatingBody', '—')])
                    ins_data.append(["Risk Rating", ins_ratings.get('InsuranceRating', '—')])
                    ins_data.append(["Rating Date", ins_ratings.get('InsuranceDate', '—')])
                    ins_data.append(["Version", ins_ratings.get('InsuranceRatingVersion', '—')])
                    ins_table = Table(ins_data, colWidths=self.table_widths['two_col'])
                    ins_table.setStyle(self.table_styles['financial'])
                    elements.append(ins_table)
                    elements.append(Spacer(1, self.spacing['table_bottom']))

                # BRI / Governing Body Ratings
                bri = risk_assessment.get('GoverningBodyRatings', {})
                if bri:
                    elements.append(Spacer(1, self.spacing['minor_section']))
                    bri_data = [["BRI Governing Body Rating", "Value"]]
                    bri_data.append(["Rating Agent", bri.get('BRIRatingAgent', '—')])
                    bri_data.append(["Version", bri.get('BRIRatingVersion', '—')])
                    bri_data.append(["Rating Date", bri.get('BRIDate', '—')])
                    bri_data.append(["Overall BRI Rating", bri.get('BRIRating', '—')])
                    bri_data.append(["Overall BRI Score", f"{bri['BRIScore']:.4f}" if isinstance(bri.get('BRIScore'), float) else '—'])
                    bri_data.append(["Flood Rating / Score", f"{bri.get('BRIFloodRating','—')} / {bri['BRIFloodScore']:.4f}" if isinstance(bri.get('BRIFloodScore'), float) else '—'])
                    bri_data.append(["Wind Rating / Score",  f"{bri.get('BRIWindRating','—')} / {bri['BRIWindScore']:.4f}"  if isinstance(bri.get('BRIWindScore'), float)  else '—'])
                    bri_data.append(["Fire Rating / Score",  f"{bri.get('BRIFireRating','—')} / {bri['BRIFireScore']:.4f}"  if isinstance(bri.get('BRIFireScore'), float)  else '—'])
                    bri_data.append(["Seismic Rating / Score", f"{bri.get('BRISeismicRating','—')} / {bri['BRISeismicScore']:.4f}" if isinstance(bri.get('BRISeismicScore'), float) else '—'])
                    bri_table = Table(bri_data, colWidths=self.table_widths['two_col'])
                    bri_table.setStyle(self.table_styles['financial'])
                    elements.append(bri_table)
                    elements.append(Spacer(1, self.spacing['table_bottom']))

                # Any remaining scalar fields
                skip = {'InsuranceBodyRatings', 'GoverningBodyRatings', 'InsurancePremium', 'ExcessAmount'}
                extra = [(k, v) for k, v in risk_assessment.items() if k not in skip and not isinstance(v, dict) and v is not None]
                if extra:
                    extra_data = [["Insurance Factor", "Details"]]
                    premium = risk_assessment.get('InsurancePremium')
                    if isinstance(premium, (int, float)):
                        extra_data.append(["Annual Insurance Premium", self._format_currency(premium)])
                    excess = risk_assessment.get('ExcessAmount')
                    if isinstance(excess, (int, float)):
                        extra_data.append(["Insurance Excess", self._format_currency(excess)])
                    for k, v in extra:
                        extra_data.append([self._format_field_name(k), self._format_value(v)])
                    extra_table = Table(extra_data, colWidths=self.table_widths['two_col'])
                    extra_table.setStyle(self.table_styles['financial'])
                    elements.append(extra_table)
                    elements.append(Spacer(1, self.spacing['table_bottom']))

            # RESILIENCE MEASURES
            resilience_measures = protection_data.get('ResilienceMeasures', {})
            if resilience_measures:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Resilience Measures", self.styles['SubSectionHeader']))

                # Coverage summary across all subsections
                all_values = [
                    v for sub in resilience_measures.values()
                    if isinstance(sub, dict) for v in sub.values()
                ]
                total_count = len(all_values)
                enhanced_count = sum(1 for v in all_values if str(v).lower() == 'enhanced')
                meets_count = sum(1 for v in all_values if 'meets' in str(v).lower())
                partial_count = sum(1 for v in all_values if str(v).lower() == 'partial')
                none_count = sum(1 for v in all_values if str(v).lower() == 'none')

                pct_full = ((enhanced_count + meets_count) / total_count * 100) if total_count else 0
                if pct_full >= 80:
                    coverage_rating = "Excellent - Comprehensive protection"
                elif pct_full >= 60:
                    coverage_rating = "Good - Well protected"
                elif pct_full >= 40:
                    coverage_rating = "Fair - Moderate protection"
                else:
                    coverage_rating = "Limited - Significant gaps present"

                summary_data = [["Protection Summary", "Count"]]
                summary_data.append(["Total Measures Assessed", str(total_count)])
                summary_data.append(["Enhanced", str(enhanced_count)])
                summary_data.append(["Meets Minimum Standard", str(meets_count)])
                summary_data.append(["Partial", str(partial_count)])
                summary_data.append(["None", str(none_count)])
                summary_data.append(["Overall Rating", coverage_rating])

                summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
                summary_table.setStyle(self.table_styles['protection'])
                elements.append(summary_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

                # Detailed measures by subsection
                _SUBSECTION_LABELS = [
                    ('FloodProtection',    'Flood Protection'),
                    ('SiteAndDrainage',    'Site & Drainage'),
                    ('BuildingAssessment', 'Building Assessment'),
                    ('FireProtection',     'Fire Protection'),
                    ('ContinuityMeasures', 'Continuity Measures'),
                ]

                for section_key, section_label in _SUBSECTION_LABELS:
                    section = resilience_measures.get(section_key, {})
                    if not section:
                        continue
                    elements.append(Spacer(1, self.spacing['minor_section']))
                    elements.append(Paragraph(section_label, self.styles['SubSectionHeader']))
                    rows = [["Measure", "Rating"]]
                    for field, value in section.items():
                        rows.append([self._format_field_name(field), str(value) if value is not None else '—'])
                    tbl = Table(rows, colWidths=self.table_widths['two_col'])
                    tbl.setStyle(self.table_styles['protection'])
                    elements.append(tbl)
                    elements.append(Spacer(1, self.spacing['table_bottom']))

            # NATURAL PROTECTION MEASURES
            natural_measures = protection_data.get('NaturalMeasures', {})
            if natural_measures:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Natural Protection Measures", self.styles['SubSectionHeader']))

                natural_installed = sum(1 for value in natural_measures.values() if value)
                natural_total = len(natural_measures)
                natural_percentage = (natural_installed / natural_total * 100) if natural_total > 0 else 0

                natural_data = [["Natural Measure", "Status"]]
                natural_data.append(["Measures Implemented", f"{natural_installed} of {natural_total} ({natural_percentage:.1f}%)"])

                # List implemented measures
                for key, value in natural_measures.items():
                    status = "✓ Implemented" if value else "✗ Not Implemented"
                    natural_data.append([self._format_field_name(key), status])

                natural_table = Table(natural_data, colWidths=self.table_widths['two_col'])
                natural_table.setStyle(self.table_styles['protection'])
                elements.append(natural_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

            # PROTECTION RECOMMENDATIONS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Protection Recommendations", self.styles['SubSectionHeader']))

            recommendations = self._generate_protection_recommendations(protection_data)

            rec_data = [[
                Paragraph("Recommendation Category", self.styles['TableHeader']),
                Paragraph("Suggested Actions", self.styles['TableHeader']),
            ]]
            normal = self.styles['Normal']
            for category, items in recommendations.items():
                item_list = items if isinstance(items, list) else [items]
                for i, action in enumerate(item_list):
                    label = Paragraph(category if i == 0 else '', normal)
                    rec_data.append([label, Paragraph(action, normal)])

            rec_table = Table(rec_data, colWidths=self.table_widths['two_col'])
            rec_table.setStyle(self.table_styles['standard'])
            elements.append(rec_table)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating protection measures: {str(e)}",
                self.styles['Normal']
            ))

        return elements

    def _generate_protection_recommendations(self, protection_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate protection recommendations based on current measures."""
        recommendations = {}

        resilience_measures = protection_data.get('ResilienceMeasures', {})

        # Flag any flood protection items rated Partial or None
        flood_prot = resilience_measures.get('FloodProtection', {})
        needs_attention = [
            f"Upgrade {self._format_field_name(k)} (currently: {v})"
            for k, v in flood_prot.items()
            if str(v).lower() in ('partial', 'none', '')
        ]
        if needs_attention:
            recommendations["Flood Protection"] = needs_attention

        # Flag site/drainage gaps
        site = resilience_measures.get('SiteAndDrainage', {})
        site_gaps = [
            f"Address {self._format_field_name(k)} (currently: {v})"
            for k, v in site.items()
            if str(v).lower() in ('partial', 'none', '')
        ]
        if site_gaps:
            recommendations["Site & Drainage"] = site_gaps

        # Insurance recommendations
        risk_assessment = protection_data.get('RiskAssessment', {})
        flood_re_eligible = risk_assessment.get('FloodReEligible')
        if flood_re_eligible:
            recommendations["Insurance"] = ["Ensure Flood Re coverage is active for affordable premiums"]

        return recommendations
