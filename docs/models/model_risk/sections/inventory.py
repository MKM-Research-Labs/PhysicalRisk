# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 2: Model Inventory Overview."""

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import (
    STEEL, RAG_COLOURS, RAG_BG, section_rule, tbl_style,
)


def build_model_inventory(data, story, S):
    story.append(Paragraph("2. Model Inventory", S['h2']))
    section_rule(story)

    models = data['models']
    if not models:
        story.append(Paragraph("No models in inventory.", S['note']))
        return

    story.append(Paragraph(
        f"{len(models)} models registered. "
        f"Tiering uses Materiality \u00d7 Complexity matrix "
        f"(Handbook Chapter 8).",
        S['body']))
    story.append(Spacer(1, 0.08 * inch))

    inv_data = [['ID', 'Name', 'Tier', 'Stage', 'RAG', 'Owner',
                 'Next Review']]
    for m in models:
        inv_data.append([
            m.get('model_id', ''),
            m.get('short_name', m.get('name', ''))[:22],
            f"T{m.get('tier', '?')}",
            m.get('lifecycle_stage', '?')[:12],
            m.get('rag_rating', '?'),
            (m.get('owner', '') or '')[:18],
            m.get('next_review_date', '\u2014') or '\u2014',
        ])

    tbl = Table(inv_data,
                colWidths=[1.05 * inch, 1.5 * inch, 0.4 * inch,
                           0.85 * inch, 0.5 * inch, 1.2 * inch, 0.9 * inch])
    ts = tbl_style()
    for row_idx, m in enumerate(models, 1):
        rag = m.get('rag_rating', '')
        col = RAG_COLOURS.get(rag, STEEL)
        bg = RAG_BG.get(rag, colors.white)
        ts.add('TEXTCOLOR', (4, row_idx), (4, row_idx), col)
        ts.add('FONTNAME', (4, row_idx), (4, row_idx), 'Helvetica-Bold')
        ts.add('BACKGROUND', (4, row_idx), (4, row_idx), bg)
    tbl.setStyle(ts)
    story.append(tbl)

    # Risk rating summary
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Composite Risk Ratings:", S['h3']))

    rr_data = [['Model', 'Score', 'Rating', 'Validation', 'Remediation',
                'Review', 'Assumptions', 'Limitations']]
    for m in models:
        orr = m.get('overall_risk_rating', {})
        cs = orr.get('component_scores', {})
        if not orr.get('calculated_score'):
            continue
        rr_data.append([
            m.get('model_id', ''),
            f"{orr.get('calculated_score', 0):.2f}",
            orr.get('effective_rating', '?'),
            f"{cs.get('validation_coverage', 0):.0%}",
            f"{cs.get('remediation_health', 0):.0%}",
            f"{cs.get('review_currency', 0):.0%}",
            f"{cs.get('assumption_risk', 0):.0%}",
            f"{cs.get('limitation_risk', 0):.0%}",
        ])

    if len(rr_data) > 1:
        tbl = Table(rr_data,
                    colWidths=[0.95 * inch, 0.55 * inch, 0.85 * inch,
                               0.75 * inch, 0.8 * inch, 0.6 * inch,
                               0.8 * inch, 0.75 * inch])
        tbl.setStyle(tbl_style())
        story.append(tbl)
