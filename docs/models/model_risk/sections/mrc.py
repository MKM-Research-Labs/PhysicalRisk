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

"""Section 4: MRC Governance Activity."""

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ..styles import GREEN, AMBER, section_rule, tbl_style


def build_mrc_activity(data, story, S):
    story.append(Paragraph("4. MRC Governance Activity", S['h2']))
    section_rule(story)

    meetings = data['meetings']
    if not meetings:
        story.append(Paragraph("No MRC meetings recorded.", S['note']))
        return

    # Meeting summary
    mtg_data = [['ID', 'Title', 'Date', 'Status', 'Decisions', 'Actions']]
    for m in meetings:
        mtg_data.append([
            m.get('id', ''),
            (m.get('title', '') or '')[:30],
            m.get('date', ''),
            m.get('status', ''),
            str(len(m.get('decisions', []))),
            str(len(m.get('actions', []))),
        ])
    tbl = Table(mtg_data,
                colWidths=[0.85 * inch, 2.0 * inch, 0.85 * inch,
                           0.85 * inch, 0.7 * inch, 0.65 * inch])
    ts = tbl_style()
    for ri, m in enumerate(meetings, 1):
        col = GREEN if m.get('status') == 'Completed' else AMBER
        ts.add('TEXTCOLOR', (3, ri), (3, ri), col)
        ts.add('FONTNAME', (3, ri), (3, ri), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)

    # Decisions from completed meetings
    all_decisions = []
    for m in meetings:
        if m.get('status') != 'Completed':
            continue
        for d in m.get('decisions', []):
            all_decisions.append((m.get('date', ''),
                                  d.get('title', d.get('decision', ''))))

    if all_decisions:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Formal Decisions Taken:", S['h3']))
        for date, title in all_decisions:
            story.append(Paragraph(
                f"&bull; <b>[{date}]</b> {title[:90]}", S['note']))

    # Open actions
    all_actions = []
    for m in meetings:
        for a in m.get('actions', []):
            if a.get('status', '').lower() not in ('completed', 'closed'):
                all_actions.append(a)

    if all_actions:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            f"Open Actions ({len(all_actions)}):", S['h3']))
        act_data = [['ID', 'Action', 'Owner', 'Due', 'Status']]
        for a in all_actions[:10]:
            act_data.append([
                a.get('id', a.get('action_id', '')),
                (a.get('title', a.get('action', '')) or '')[:50],
                (a.get('owner', '') or '')[:18],
                a.get('due_date', '\u2014') or '\u2014',
                a.get('status', ''),
            ])
        tbl = Table(act_data,
                    colWidths=[0.6 * inch, 2.6 * inch, 1.2 * inch,
                               0.85 * inch, 0.85 * inch])
        tbl.setStyle(tbl_style())
        story.append(tbl)
