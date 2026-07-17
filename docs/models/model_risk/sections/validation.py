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

"""Section 3: Model Validation Status."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import GREEN, AMBER, RED, section_rule, tbl_style


def build_validation_status(data, story, S):
    story.append(Paragraph("3. Model Validation Status", S['h2']))
    section_rule(story)

    models = data['models']

    # Collect unique validation questions
    all_questions = []
    for m in models:
        for q in m.get('validation_questions', []):
            if q.get('short_label') and q['short_label'] not in all_questions:
                all_questions.append(q['short_label'])

    if all_questions:
        story.append(Paragraph(
            "Validation Questions (9 per model, per Handbook Chapter 5):",
            S['h3']))

        vq_header = ['Model'] + [q[:12] for q in all_questions]
        vq_data = [vq_header]

        status_map = {
            'Addressed': '\u2713',
            'Partially Addressed': '\u25cb',
            'Not Addressed': '\u2717',
            'Not Applicable': 'N/A',
        }

        for m in models:
            questions = {q.get('short_label', ''): q.get('status', '')
                         for q in m.get('validation_questions', [])}
            if not questions:
                continue
            row = [m.get('model_id', '')]
            for ql in all_questions:
                st = questions.get(ql, '')
                row.append(status_map.get(st, '\u2014'))
            vq_data.append(row)

        if len(vq_data) > 1:
            n_cols = len(vq_header)
            q_width = min(0.65, 5.5 / max(n_cols - 1, 1))
            col_widths = [1.0 * inch] + [q_width * inch] * (n_cols - 1)
            tbl = Table(vq_data, colWidths=col_widths)
            ts = tbl_style()
            for ri, m in enumerate(models, 1):
                questions = {q.get('short_label', ''): q.get('status', '')
                             for q in m.get('validation_questions', [])}
                if not questions:
                    continue
                for ci, ql in enumerate(all_questions, 1):
                    st = questions.get(ql, '')
                    if st == 'Addressed':
                        ts.add('TEXTCOLOR', (ci, ri), (ci, ri), GREEN)
                    elif st == 'Partially Addressed':
                        ts.add('TEXTCOLOR', (ci, ri), (ci, ri), AMBER)
                    elif st == 'Not Addressed':
                        ts.add('TEXTCOLOR', (ci, ri), (ci, ri), RED)
                    ts.add('ALIGN', (ci, ri), (ci, ri), 'CENTER')
            tbl.setStyle(ts)
            story.append(tbl)

    # High-impact assumptions
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Key Assumptions (High Impact):", S['h3']))
    high_assumptions = []
    for m in models:
        for a in m.get('assumptions', []):
            if a.get('impact') == 'High':
                high_assumptions.append((m.get('model_id', ''),
                                         a.get('id', ''),
                                         a.get('description', '')))

    if high_assumptions:
        a_data = [['Model', 'ID', 'Assumption']]
        for mid, aid, desc in high_assumptions[:15]:
            a_data.append([mid, aid, desc[:80]])
        tbl = Table(a_data,
                    colWidths=[0.95 * inch, 0.6 * inch, 4.85 * inch])
        tbl.setStyle(tbl_style())
        story.append(tbl)
    else:
        story.append(Paragraph(
            "No high-impact assumptions flagged.", S['note']))

    # Peer reviewer gaps
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Peer Reviewer Assignments:", S['h3']))
    gaps = [m.get('model_id', '') for m in models
            if not m.get('peer_reviewer') or m['peer_reviewer'] == 'TBD']
    if gaps:
        story.append(Paragraph(
            f"<b>{len(gaps)} model(s) without assigned peer reviewer:</b> "
            + ', '.join(gaps),
            S['body']))
    else:
        story.append(Paragraph(
            "All models have assigned peer reviewers.", S['note']))
