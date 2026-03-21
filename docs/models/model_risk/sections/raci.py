# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 7: RACI & Escalation Framework."""

from collections import Counter

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import AMBER, section_rule, tbl_style


def build_raci(data, story, S):
    story.append(Paragraph("7. RACI &amp; Escalation Framework", S['h2']))
    section_rule(story)

    raci = data['raci']
    roles = raci.get('roles', [])
    activities = raci.get('activities', [])

    if not roles:
        story.append(Paragraph("RACI matrix not available.", S['note']))
        return

    # Role assignments
    story.append(Paragraph("Role Assignments:", S['h3']))
    role_data = [['Role', 'RACI', 'Assigned To', 'Backup']]
    for r in roles:
        role_data.append([
            r.get('label', ''),
            r.get('raci_code', ''),
            r.get('assigned_to', '\u2014') or '\u2014',
            r.get('backup', '\u2014') or '\u2014',
        ])
    tbl = Table(role_data,
                colWidths=[1.8 * inch, 0.6 * inch, 1.8 * inch, 1.8 * inch])
    ts = tbl_style()
    # Highlight missing backups
    for ri, r in enumerate(roles, 1):
        if not r.get('backup'):
            ts.add('TEXTCOLOR', (3, ri), (3, ri), AMBER)
    tbl.setStyle(ts)
    story.append(tbl)

    # Activities summary by category
    if activities:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Activity Coverage:", S['h3']))
        cats = Counter(a.get('category', '?') for a in activities)
        story.append(Paragraph(
            f"{len(activities)} activities across "
            f"{len(cats)} categories: " +
            ', '.join(f"{c} ({n})" for c, n in cats.most_common()),
            S['body']))

    # Escalation triggers
    triggers = raci.get('escalation_triggers', [])
    if triggers:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            f"Escalation Triggers ({len(triggers)}):", S['h3']))
        for t in triggers[:6]:
            trigger_text = t if isinstance(t, str) else t.get(
                'trigger', t.get('description', str(t)))
            story.append(Paragraph(f"&bull; {trigger_text[:100]}", S['note']))
