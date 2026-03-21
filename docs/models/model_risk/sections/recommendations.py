# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Section 11: Recommendations & Roadmap."""

from datetime import datetime

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer

from ..styles import section_rule


def build_recommendations(data, story, S):
    story.append(Paragraph("11. Recommendations &amp; Roadmap", S['h2']))
    section_rule(story)

    recommendations = []
    models = data['models']
    today = datetime.now().strftime('%Y-%m-%d')

    # Validation gaps
    vq_total = sum(len(m.get('validation_questions', [])) for m in models)
    vq_addressed = sum(
        1 for m in models
        for q in m.get('validation_questions', [])
        if q.get('status') in ('Addressed', 'Partially Addressed')
    )
    if vq_total > 0 and vq_addressed < vq_total:
        recommendations.append(
            f"<b>Validation Questions:</b> {vq_total - vq_addressed} of "
            f"{vq_total} validation questions unanswered. "
            f"Address per Handbook Chapter 5 before next MRC.")

    # Peer reviewer gaps
    gaps = [m.get('model_id', '') for m in models
            if not m.get('peer_reviewer') or m['peer_reviewer'] == 'TBD']
    if gaps:
        recommendations.append(
            f"<b>Peer Reviewers:</b> {len(gaps)} model(s) without assigned "
            f"peer reviewer ({', '.join(gaps[:5])}). "
            f"Assign per SR 11-7 independent review requirements.")

    # Overdue remediation
    overdue = [
        (m.get('model_id', ''), r.get('id', ''))
        for m in models
        for r in m.get('remediation_steps', [])
        if r.get('status', '').lower() in ('open', 'in progress')
        and (r.get('due_date', '9999') or '9999') < today
    ]
    if overdue:
        recommendations.append(
            f"<b>Overdue Remediation:</b> {len(overdue)} item(s) past due "
            f"date. Escalate to MRC for re-prioritisation.")

    # BCBS at-risk
    at_risk = [p for p in data['bcbs'].get('principles', [])
               if p.get('score', 0) <= 2]
    if at_risk:
        recommendations.append(
            f"<b>BCBS 239:</b> {len(at_risk)} principle(s) rated Materially "
            f"Non-compliant: " +
            ', '.join(f"P{p['id']}" for p in at_risk) +
            ". Target remediation dates are set — track at MRC.")

    # Missing backups in RACI
    raci_gaps = [r.get('label', '') for r in data['raci'].get('roles', [])
                 if not r.get('backup')]
    if raci_gaps:
        recommendations.append(
            f"<b>RACI Backup Coverage:</b> {len(raci_gaps)} role(s) without "
            f"backup assignment ({', '.join(raci_gaps)}). "
            f"Single points of failure in governance.")

    # Test failures
    junit = data['junit']
    if junit['failed'] > 0:
        recommendations.append(
            f"<b>Test Failures:</b> {junit['failed']} test(s) failing. "
            f"Resolve before next release.")

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", S['body']))
            story.append(Spacer(1, 0.06 * inch))
    else:
        story.append(Paragraph(
            "<b>No critical recommendations.</b> All governance processes "
            "are current and compliant.",
            S['body']))
