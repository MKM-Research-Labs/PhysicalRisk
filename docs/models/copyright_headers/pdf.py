# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Render the copyright-header audit findings into a PDF report."""

import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

from docs.models.hardcoding.pdf_helpers import (
    _risk_label, _styles, _header_style, _section_rule,
)

# The per-file remediation table can run to thousands of rows on the first
# sweep; cap the rendered detail and state how many were omitted rather than
# silently truncating.
_MAX_DETAIL_ROWS = 400


def _short(text: str, limit: int = 70) -> str:
    """First line of an old header block, trimmed for a table cell."""
    first = (text or '').splitlines()[0] if text else ''
    first = first.strip()
    return (first[:limit] + '…') if len(first) > limit else first


def _detail_table(rows):
    data = [['File', 'a) Wrong header', 'b) Replaced', 'c) Now compatible']]
    for item in rows:
        data.append([
            item['file'],
            _short(item.get('old_header', '')),
            'YES',
            'YES' if item.get('now_compliant') else 'NO',
        ])
    t = Table(data, colWidths=[2.7 * inch, 2.3 * inch, 0.8 * inch, 1.0 * inch])
    t.setStyle(_header_style())
    return t


def create_pdf_report(findings: dict, output_path: Path, root: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    S = _styles()
    story = []

    fixed = findings.get('fixed', [])
    remaining = findings.get('remaining', [])
    scanned = findings.get('scanned', 0)
    compliant = findings.get('already_compliant', 0)

    # ------------------------------------------------------------------ Title
    story.append(Paragraph("Copyright Header Audit Report", S['title']))
    story.append(Paragraph(
        "License-Header Governance — All First-Party .py and .js Source", S['h3']))
    story.append(Spacer(1, 0.1 * inch))

    meta = (
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"&nbsp;&nbsp;&nbsp;<b>Project Root:</b> {root}<br/>"
        f"<b>Scope:</b> Every tracked .py and .js file (excluding vendored "
        f"dirs, caches, the data symlink and sibling worktrees)<br/>"
        f"<b>Canonical Source:</b> docs/shared/copyright.py (exact 19-line "
        f"MKM Research Labs license header)<br/>"
        f"<b>Policy:</b> Each source file must begin with the canonical header "
        f"byte-for-byte (after an optional shebang).  This audit is "
        f"self-healing: non-compliant headers are rewritten in place."
    )
    story.append(Paragraph(meta, S['body']))

    # -------------------------------------------------------- Executive summary
    _section_rule(story)
    story.append(Paragraph("Executive Summary", S['h2']))
    summary_data = [
        ['Metric', 'Count', 'Status'],
        ['Files scanned', str(scanned), ''],
        ['Already compliant', str(compliant), _risk_label(0)],
        ['Headers replaced (now compatible)', str(len(fixed)),
         'REVIEW' if fixed else _risk_label(0)],
        ['Still non-compliant', str(len(remaining)), _risk_label(len(remaining))],
    ]
    tbl = Table(summary_data, colWidths=[3.6 * inch, 1.2 * inch, 1.6 * inch])
    ts = _header_style()
    for row_idx, row in enumerate(summary_data[1:], 1):
        status = row[2]
        colour = {
            'COMPLIANT': '#27ae60',
            'ACTION REQUIRED': '#c0392b',
            'REVIEW': '#e67e22',
        }.get(status)
        if colour:
            ts.add('TEXTCOLOR', (2, row_idx), (2, row_idx), colors.HexColor(colour))
            ts.add('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)
    story.append(Spacer(1, 0.2 * inch))

    if not remaining and not fixed:
        story.append(Paragraph(
            "<b>RESULT: COMPLIANT.</b>  Every .py and .js file already carries "
            "the canonical license header.  Nothing was changed.", S['body']))
    elif not remaining:
        story.append(Paragraph(
            f"<b>RESULT: REMEDIATED.</b>  {len(fixed)} file(s) had a wrong or "
            f"missing header; each was replaced with the canonical header and "
            f"is now compatible.  No file remains non-compliant.", S['body']))
    else:
        story.append(Paragraph(
            f"<b>RESULT: ACTION REQUIRED.</b>  {len(remaining)} file(s) could "
            f"not be made compliant automatically (see Section 2).", S['body']))

    # ---------------------------------------------- Section 1 — replaced headers
    story.append(PageBreak())
    story.append(Paragraph("1. Headers Replaced", S['h2']))
    story.append(Paragraph(
        "For each file below the original header (a) was wrong or missing, it "
        "(b) was replaced with the canonical header, and the file is (c) now "
        "compatible.", S['body']))
    story.append(Spacer(1, 0.1 * inch))
    if not fixed:
        story.append(Paragraph("No headers needed replacing. COMPLIANT.", S['note']))
    else:
        shown = fixed[:_MAX_DETAIL_ROWS]
        story.append(_detail_table(shown))
        if len(fixed) > _MAX_DETAIL_ROWS:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(
                f"… and {len(fixed) - _MAX_DETAIL_ROWS} further file(s) replaced "
                f"(omitted from this table for length; all are now compatible).",
                S['note']))

    # -------------------------------------------- Section 2 — still non-compliant
    if remaining:
        _section_rule(story)
        story.append(Paragraph("2. Still Non-Compliant", S['h2']))
        story.append(Paragraph(
            "These files could not be repaired automatically and need manual "
            "attention.", S['body']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(_detail_table(remaining[:_MAX_DETAIL_ROWS]))

    _section_rule(story)
    story.append(Paragraph(
        "<i>Report generated by docs.models.copyright_headers — "
        "MKM Research Labs Physical Risk Platform</i>", S['note']))

    doc.build(story)
    print(f"  copyright_headers_report.pdf written to {output_path}")
