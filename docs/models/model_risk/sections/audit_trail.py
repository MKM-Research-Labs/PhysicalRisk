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
