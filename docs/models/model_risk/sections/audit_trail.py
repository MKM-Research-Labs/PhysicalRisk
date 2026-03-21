# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 9: Audit Trail Statistics."""

from collections import Counter

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import section_rule, tbl_style


def build_audit_trail(data, story, S):
    story.append(Paragraph("9. Audit Trail Statistics", S['h2']))
    section_rule(story)

    log = data['audit_log']
    if not log:
        story.append(Paragraph("No audit trail entries.", S['note']))
        return

    story.append(Paragraph(
        f"<b>{len(log)}</b> events logged.", S['body']))
    story.append(Spacer(1, 0.08 * inch))

    # By model
    by_model = Counter(e.get('model_id', '?') for e in log)
    story.append(Paragraph("Events by Model:", S['h3']))
    model_data = [['Model ID', 'Events', 'Share']]
    for mid, count in by_model.most_common():
        model_data.append([
            mid, str(count),
            f"{100 * count / len(log):.1f}%",
        ])
    tbl = Table(model_data,
                colWidths=[1.5 * inch, 1.0 * inch, 1.0 * inch])
    tbl.setStyle(tbl_style())
    story.append(tbl)

    # Date range
    if log:
        dates = [e.get('timestamp', '')[:10] for e in log if e.get('timestamp')]
        if dates:
            story.append(Spacer(1, 0.06 * inch))
            story.append(Paragraph(
                f"Date range: {min(dates)} to {max(dates)}",
                S['note']))
