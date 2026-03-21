# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Cover page."""

from collections import Counter
from datetime import datetime

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer


def build_cover(data, story, S):
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("Model Risk Governance Report", S['title']))
    story.append(Paragraph(
        "MRC Evidence Package \u2014 SR 11-7 / SS1/23 / BCBS 239",
        S['subtitle']))
    story.append(Spacer(1, 0.3 * inch))

    models = data['models']
    tiers = Counter(m.get('tier', '?') for m in models)
    rags = Counter(m.get('rag_rating', '?') for m in models)

    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        S['meta']))
    story.append(Paragraph(
        f"<b>Models:</b> {len(models)} | "
        f"<b>Tier 1:</b> {tiers.get(1, 0)} | "
        f"<b>Tier 2:</b> {tiers.get(2, 0)} | "
        f"<b>Tier 3:</b> {tiers.get(3, 0)}",
        S['meta']))
    story.append(Paragraph(
        f"<b>RAG:</b> "
        f"Green {rags.get('Green', 0)} | "
        f"Amber {rags.get('Amber', 0)} | "
        f"Red {rags.get('Red', 0)}",
        S['meta']))

    bcbs = data['bcbs']
    principles = bcbs.get('principles', [])
    if principles:
        total_score = sum(p.get('score', 0) for p in principles)
        max_score = sum(p.get('max_score', 4) for p in principles)
        story.append(Paragraph(
            f"<b>BCBS 239 Compliance:</b> {total_score}/{max_score} "
            f"({100 * total_score / max(max_score, 1):.0f}%)",
            S['meta']))

    junit = data['junit']
    if junit['total'] > 0:
        cov = data.get('coverage_pct')
        cov_str = f" | Coverage: {cov:.1f}%" if cov else ""
        story.append(Paragraph(
            f"<b>Tests:</b> {junit['passed']}/{junit['total']} passed"
            f"{cov_str}",
            S['meta']))

    story.append(Spacer(1, 0.5 * inch))
    meta = data['inventory'].get('metadata', {})
    story.append(Paragraph(
        f"<i>Framework: {meta.get('framework', 'MKM Research Labs')}<br/>"
        f"Reference: {meta.get('handbook_reference', '')}</i>",
        S['note']))
