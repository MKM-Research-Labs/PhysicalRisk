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

"""Section 6: BCBS 239 Compliance Summary."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import GREEN, AMBER, RED, section_rule, tbl_style


def build_bcbs239(data, story, S):
    story.append(Paragraph("6. BCBS 239 Compliance", S['h2']))
    section_rule(story)

    bcbs = data['bcbs']
    principles = bcbs.get('principles', [])
    if not principles:
        story.append(Paragraph(
            "BCBS 239 assessment not available.", S['note']))
        return

    total_score = sum(p.get('score', 0) for p in principles)
    max_score = sum(p.get('max_score', 4) for p in principles)
    pct = 100 * total_score / max(max_score, 1)

    story.append(Paragraph(
        f"Overall compliance: <b>{total_score}/{max_score} ({pct:.0f}%)</b> | "
        f"Assessed: {bcbs.get('assessment_date', '?')} | "
        f"Assessor: {bcbs.get('assessor', '?')}",
        S['body']))
    story.append(Spacer(1, 0.08 * inch))

    bcbs_data = [['#', 'Principle', 'Category', 'Score', 'Status']]
    for p in principles:
        bcbs_data.append([
            str(p.get('id', '')),
            p.get('title', ''),
            p.get('category', '')[:25],
            f"{p.get('score', 0)}/{p.get('max_score', 4)}",
            p.get('status', ''),
        ])

    tbl = Table(bcbs_data,
                colWidths=[0.3 * inch, 1.8 * inch, 1.6 * inch,
                           0.6 * inch, 1.8 * inch])
    ts = tbl_style()
    for ri, p in enumerate(principles, 1):
        score = p.get('score', 0)
        col = GREEN if score >= 3 else AMBER if score == 2 else RED
        ts.add('TEXTCOLOR', (3, ri), (3, ri), col)
        ts.add('FONTNAME', (3, ri), (3, ri), 'Helvetica-Bold')
        ts.add('TEXTCOLOR', (4, ri), (4, ri), col)
    tbl.setStyle(ts)
    story.append(tbl)

    # Call out at-risk principles
    at_risk = [p for p in principles if p.get('score', 0) <= 2]
    if at_risk:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Principles Requiring Attention:", S['h3']))
        for p in at_risk:
            story.append(Paragraph(
                f"&bull; <b>P{p['id']} {p['title']}:</b> "
                f"{p.get('gaps', 'No gaps documented')}",
                S['note']))
