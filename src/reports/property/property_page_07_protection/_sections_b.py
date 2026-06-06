# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Resilience, natural-measure, and recommendation sections of page 7."""

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer, Table


class _SectionsBMixin:
    """Resilience / natural-measure tables and protection recommendations."""

    def _add_resilience_measures(self, elements: list, protection_data: Dict[str, Any]) -> None:
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

    def _add_natural_measures(self, elements: list, protection_data: Dict[str, Any]) -> None:
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

    def _add_recommendations(self, elements: list, protection_data: Dict[str, Any]) -> None:
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

    def _generate_protection_recommendations(self, protection_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate protection recommendations based on current measures.

        Handles two data shapes that appear in different parts of the
        codebase:

        - **Nested** (production): ``ResilienceMeasures.FloodProtection.<key>``
          carries a rating string (Enhanced/Meets/Partial/None). Partial/None
          ratings drive the "Flood Protection" and "Site & Drainage" categories.
        - **Flat boolean** (legacy + tests): ``ResilienceMeasures.<key>`` /
          ``NaturalMeasures.<key>`` carries a bool. A False value drives the
          "Priority Installations" and "Natural Solutions" categories.

        Plus a Flood-Re flag on the RiskAssessment sub-dict drives the
        "Insurance" category.
        """
        recommendations = {}

        resilience_measures = protection_data.get('ResilienceMeasures', {})

        # --- Nested rating-shape (production) ---
        flood_prot = resilience_measures.get('FloodProtection', {})
        needs_attention = [
            f"Upgrade {self._format_field_name(k)} (currently: {v})"
            for k, v in flood_prot.items()
            if str(v).lower() in ('partial', 'none', '')
        ]
        if needs_attention:
            recommendations["Flood Protection"] = needs_attention

        site = resilience_measures.get('SiteAndDrainage', {})
        site_gaps = [
            f"Address {self._format_field_name(k)} (currently: {v})"
            for k, v in site.items()
            if str(v).lower() in ('partial', 'none', '')
        ]
        if site_gaps:
            recommendations["Site & Drainage"] = site_gaps

        # --- Flat boolean shape ---
        # Top-level False entries directly under ResilienceMeasures are
        # treated as missing critical installations.
        missing_critical = [
            f"Install {self._format_field_name(k)}"
            for k, v in resilience_measures.items()
            if not isinstance(v, dict) and v is False
        ]
        if missing_critical:
            recommendations["Priority Installations"] = missing_critical

        # Same convention for NaturalMeasures.
        natural_measures = protection_data.get('NaturalMeasures', {})
        missing_natural = [
            f"Consider {self._format_field_name(k)}"
            for k, v in natural_measures.items()
            if not isinstance(v, dict) and v is False
        ]
        if missing_natural:
            recommendations["Natural Solutions"] = missing_natural

        # --- Insurance ---
        risk_assessment = protection_data.get('RiskAssessment', {})
        flood_re_eligible = risk_assessment.get('FloodReEligible')
        if flood_re_eligible:
            recommendations["Insurance"] = ["Ensure Flood Re coverage is active for affordable premiums"]

        return recommendations
