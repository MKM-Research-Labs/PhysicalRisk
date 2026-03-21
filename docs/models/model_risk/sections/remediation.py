# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 5: Remediation Tracker."""

from collections import Counter
from datetime import datetime

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import GREEN, AMBER, RED, STEEL, LIGHT_RED, section_rule, tbl_style


def build_remediation(data, story, S):
    story.append(Paragraph("5. Remediation Tracker", S['h2']))
    section_rule(story)

    models = data['models']
    today = datetime.now().strftime('%Y-%m-%d')

    all_rems = []
    for m in models:
        for r in m.get('remediation_steps', []):
            r_copy = dict(r)
            r_copy['model_id'] = m.get('model_id', '')
            r_copy['overdue'] = (
                r.get('status', '').lower() in ('open', 'in progress')
                and (r.get('due_date', '9999') or '9999') < today
            )
            all_rems.append(r_copy)

    if not all_rems:
        story.append(Paragraph("No remediation items recorded.", S['note']))
        return

    # Summary by status
    by_status = Counter(r.get('status', '?') for r in all_rems)
    overdue_count = sum(1 for r in all_rems if r.get('overdue'))

    story.append(Paragraph(
        f"<b>{len(all_rems)}</b> total items | "
        f"Open: {by_status.get('Open', 0)} | "
        f"In Progress: {by_status.get('In Progress', 0)} | "
        f"Completed: {by_status.get('Completed', 0)} | "
        f"<b>Overdue: {overdue_count}</b>",
        S['body']))
    story.append(Spacer(1, 0.08 * inch))

    def _sort_key(x):
        return (
            {'High': 0, 'Medium': 1, 'Low': 2}.get(x.get('priority'), 3),
            x.get('due_date', '9999'),
        )

    # Full table
    rem_data = [['Model', 'ID', 'Description', 'Priority', 'Due',
                 'Status']]
    sorted_rems = sorted(all_rems, key=_sort_key)
    for r in sorted_rems:
        rem_data.append([
            r.get('model_id', ''),
            r.get('id', ''),
            (r.get('description', '') or '')[:45],
            r.get('priority', ''),
            r.get('due_date', '\u2014') or '\u2014',
            r.get('status', ''),
        ])

    tbl = Table(rem_data,
                colWidths=[0.9 * inch, 0.55 * inch, 2.4 * inch,
                           0.65 * inch, 0.8 * inch, 0.8 * inch])
    ts = tbl_style()
    for ri, r in enumerate(sorted_rems, 1):
        # Highlight overdue
        if r.get('overdue'):
            ts.add('BACKGROUND', (0, ri), (-1, ri), LIGHT_RED)
            ts.add('TEXTCOLOR', (5, ri), (5, ri), RED)
            ts.add('FONTNAME', (5, ri), (5, ri), 'Helvetica-Bold')
        # Priority colour
        pri_col = {'High': RED, 'Medium': AMBER, 'Low': GREEN}.get(
            r.get('priority'), STEEL)
        ts.add('TEXTCOLOR', (3, ri), (3, ri), pri_col)
        ts.add('FONTNAME', (3, ri), (3, ri), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)
