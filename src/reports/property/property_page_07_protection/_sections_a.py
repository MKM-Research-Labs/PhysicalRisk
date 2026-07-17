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

"""Hazard-profile and insurance/risk-assessment sections of page 7."""

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer, Table


class _SectionsAMixin:
    """Hazard profile + insurance/risk-assessment table builders."""

    def _add_hazard_profile(self, elements: list, protection_data: Dict[str, Any]) -> None:
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

            # OPERATIONAL THRESHOLDS — only render if at least one is set.
            # Wind in m/s, Water/Flash in m above local gauge Severe level.
            _THRESHOLD_FIELDS = [
                ('WindThresholdMajorMps',  'Wind Major (m/s)'),
                ('WindThresholdMinorMps',  'Wind Minor (m/s)'),
                ('WaterThresholdMajorM',   'Water Major (m over Severe)'),
                ('WaterThresholdMinorM',   'Water Minor (m over Severe)'),
                ('FlashThresholdMajorM',   'Flash Major (m over Severe)'),
                ('FlashThresholdMinorM',   'Flash Minor (m over Severe)'),
            ]
            threshold_rows = [
                (label, hazard_profile.get(key))
                for key, label in _THRESHOLD_FIELDS
                if hazard_profile.get(key) is not None
            ]
            if threshold_rows:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Operational Thresholds", self.styles['SubSectionHeader']))
                th_data = [["Threshold", "Value"]]
                for label, value in threshold_rows:
                    if isinstance(value, (int, float)):
                        th_data.append([label, f"{value:.2f}"])
                    else:
                        th_data.append([label, str(value)])
                th_table = Table(th_data, colWidths=self.table_widths['two_col'])
                th_table.setStyle(self.table_styles['protection'])
                elements.append(th_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

    def _add_risk_assessment(self, elements: list, protection_data: Dict[str, Any]) -> None:
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

                def _rating_score(rating_key: str, score_key: str) -> str:
                    rating = bri.get(rating_key, '—') or '—'
                    score = bri.get(score_key)
                    if isinstance(score, float):
                        return f"{rating} / {score:.4f}"
                    return f"{rating} / —"

                bri_data = [["BRI Governing Body Rating", "Value"]]
                bri_data.append(["Rating Agent", bri.get('BRIRatingAgent', '—')])
                bri_data.append(["Version", bri.get('BRIRatingVersion', '—')])
                bri_data.append(["Rating Date", bri.get('BRIDate', '—')])
                bri_data.append(["Overall BRI Rating", bri.get('BRIRating', '—')])
                bri_data.append(["Overall BRI Score", f"{bri['BRIScore']:.4f}" if isinstance(bri.get('BRIScore'), float) else '—'])
                bri_data.append(["Wind Rating / Score",      _rating_score('BRIWindRating',    'BRIWindScore')])
                bri_data.append(["Flood (envelope) Rating / Score", _rating_score('BRIFloodRating', 'BRIFloodScore')])
                # Water + Flash split-ratings only render when populated
                # (commercial today; residential leaves them null).
                if bri.get('BRIWaterRating') is not None or bri.get('BRIWaterScore') is not None:
                    bri_data.append(["Water (Tsunami / Surge) Rating / Score",
                                     _rating_score('BRIWaterRating', 'BRIWaterScore')])
                if bri.get('BRIFlashRating') is not None or bri.get('BRIFlashScore') is not None:
                    bri_data.append(["Flash Flood / Fluvial Rating / Score",
                                     _rating_score('BRIFlashRating', 'BRIFlashScore')])
                bri_data.append(["Fire Rating / Score",    _rating_score('BRIFireRating',    'BRIFireScore')])
                bri_data.append(["Seismic Rating / Score", _rating_score('BRISeismicRating', 'BRISeismicScore')])
                bri_table = Table(bri_data, colWidths=self.table_widths['two_col'])
                bri_table.setStyle(self.table_styles['financial'])
                elements.append(bri_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))

                # INDUSTRY GROUPS — BRI measure-code lists by hazard.
                # Only render when at least one list is non-empty.
                industry = bri.get('IndustryGroups', {}) or {}
                _GROUP_FIELDS = [
                    ('WindCodes',    'Wind Codes'),
                    ('WaterCodes',   'Water (Tsunami / Surge) Codes'),
                    ('FlashCodes',   'Flash Flood / Fluvial Codes'),
                    ('FireCodes',    'Fire Codes'),
                    ('SeismicCodes', 'Seismic Codes'),
                ]
                group_rows = [
                    (label, industry.get(key))
                    for key, label in _GROUP_FIELDS
                    if industry.get(key)
                ]
                if group_rows:
                    elements.append(Spacer(1, self.spacing['minor_section']))
                    elements.append(Paragraph("BRI Measure Codes (Industry Groups)",
                                              self.styles['SubSectionHeader']))
                    ig_data = [["Hazard", "Codes"]]
                    for label, codes in group_rows:
                        ig_data.append([label, ", ".join(codes)])
                    ig_table = Table(ig_data, colWidths=self.table_widths['two_col'])
                    ig_table.setStyle(self.table_styles['protection'])
                    elements.append(ig_table)
                    elements.append(Spacer(1, self.spacing['table_bottom']))

            # Insurance scalars (Premium, Excess) + any remaining scalar fields
            # are collected into a single "Insurance Factor" table. The table
            # is rendered whenever ANY of those scalars is present — earlier
            # versions skipped the whole table if `extra` was empty, which
            # meant a property with only InsurancePremium produced no output.
            skip = {'InsuranceBodyRatings', 'GoverningBodyRatings',
                    'InsurancePremium', 'ExcessAmount'}
            extra = [(k, v) for k, v in risk_assessment.items()
                     if k not in skip and not isinstance(v, dict) and v is not None]
            premium = risk_assessment.get('InsurancePremium')
            excess = risk_assessment.get('ExcessAmount')
            if extra or isinstance(premium, (int, float)) or isinstance(excess, (int, float)):
                extra_data = [["Insurance Factor", "Details"]]
                if isinstance(premium, (int, float)):
                    extra_data.append(["Annual Insurance Premium",
                                       self._format_currency(premium)])
                if isinstance(excess, (int, float)):
                    extra_data.append(["Insurance Excess",
                                       self._format_currency(excess)])
                for k, v in extra:
                    extra_data.append([self._format_field_name(k),
                                       self._format_value(v)])
                extra_table = Table(extra_data, colWidths=self.table_widths['two_col'])
                extra_table.setStyle(self.table_styles['financial'])
                elements.append(extra_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
