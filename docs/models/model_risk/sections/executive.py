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

"""Section 1: Executive Summary."""

from datetime import datetime

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table

from ..styles import GREEN, AMBER, RED, STEEL, section_rule, tbl_style


def build_exec_summary(data, story, S):
    story.append(Paragraph("1. Executive Summary", S['h2']))
    section_rule(story)

    models = data['models']
    meetings = data['meetings']
    junit = data['junit']
    today = datetime.now().strftime('%Y-%m-%d')

    total_rems = sum(len(m.get('remediation_steps', [])) for m in models)
    open_rems = sum(
        1 for m in models
        for r in m.get('remediation_steps', [])
        if r.get('status', '').lower() in ('open', 'in progress')
    )
    overdue_rems = sum(
        1 for m in models
        for r in m.get('remediation_steps', [])
        if r.get('status', '').lower() in ('open', 'in progress')
        and (r.get('due_date', '9999') or '9999') < today
    )
    completed_meetings = sum(
        1 for m in meetings if m.get('status') == 'Completed')
    total_decisions = sum(len(m.get('decisions', [])) for m in meetings)
    total_actions = sum(len(m.get('actions', [])) for m in meetings)

    vq_total = sum(len(m.get('validation_questions', [])) for m in models)
    vq_addressed = sum(
        1 for m in models
        for q in m.get('validation_questions', [])
        if q.get('status') in ('Addressed', 'Partially Addressed')
    )
    peers_assigned = sum(
        1 for m in models
        if m.get('peer_reviewer') and m['peer_reviewer'] != 'TBD'
    )

    summary = [
        ['Area', 'Metric', 'Value', 'Status'],
        ['Inventory', 'Total models', str(len(models)), 'INFO'],
        ['Inventory', 'Models in Production',
         str(sum(1 for m in models
                 if m.get('lifecycle_stage') == 'Production')),
         'INFO'],
        ['Validation', 'Validation questions addressed',
         f'{vq_addressed}/{vq_total}',
         'REVIEW' if vq_total > 0 and vq_addressed < vq_total else 'PASS'],
        ['Validation', 'Peer reviewers assigned',
         f'{peers_assigned}/{len(models)}',
         'REVIEW' if peers_assigned < len(models) else 'PASS'],
        ['MRC', 'Meetings held', str(completed_meetings),
         'PASS' if completed_meetings > 0 else 'REVIEW'],
        ['MRC', 'Formal decisions', str(total_decisions), 'INFO'],
        ['MRC', 'Open actions', str(total_actions), 'INFO'],
        ['Remediation', 'Total items', str(total_rems), 'INFO'],
        ['Remediation', 'Open / In Progress', str(open_rems),
         'REVIEW' if open_rems > 0 else 'PASS'],
        ['Remediation', 'Overdue', str(overdue_rems),
         'FAIL' if overdue_rems > 0 else 'PASS'],
        ['Testing', 'Test pass rate',
         f"{junit['passed']}/{junit['total']}" if junit['total'] else 'N/A',
         'PASS' if junit['failed'] == 0 and junit['total'] > 0 else (
             'FAIL' if junit['failed'] > 0 else 'NOT RUN')],
        ['Testing', 'Code coverage',
         f"{data['coverage_pct']:.1f}%" if data.get('coverage_pct') else 'N/A',
         'PASS' if (data.get('coverage_pct') or 0) >= 70 else 'REVIEW'],
        ['Audit', 'Audit trail events', str(len(data['audit_log'])),
         'PASS' if len(data['audit_log']) > 0 else 'REVIEW'],
        ['Audit', 'Governance reports available',
         str(len(data['audit_files'])), 'INFO'],
    ]

    tbl = Table(summary,
                colWidths=[1.2 * inch, 2.0 * inch, 1.2 * inch, 1.2 * inch])
    ts = tbl_style()
    for row_idx, row in enumerate(summary[1:], 1):
        status = row[3]
        col = (GREEN if status == 'PASS' else
               AMBER if status == 'REVIEW' else
               RED if status == 'FAIL' else STEEL)
        ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), col)
        ts.add('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)
