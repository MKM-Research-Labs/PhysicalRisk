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

"""Render the json-file audit findings into a standalone PDF report.

Reuses the §4.5 scanner (``scan_repo`` / ``_build_json_files``) and the full-audit
styling so the standalone report and the consolidated audit stay visually and
numerically identical."""

from collections import Counter, defaultdict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from reportlab.lib.colors import HexColor

from docs.models.full_audit._constants import NAVY, GREEN, RED, GREY
from docs.models.full_audit.styles import _styles
from docs.models.full_audit.helpers import _header_footer
from docs.models.full_audit.sections_tests.json_files import GATED

_ROW_ALT = HexColor('#F4F6FA')

_TABLE_STYLE = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
    ('TEXTCOLOR', (0, 0), (-1, 0), GREY),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.4, GREY),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, _ROW_ALT]),
    ('TOPPADDING', (0, 0), (-1, -1), 2),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
])


def _area(path: str) -> str:
    parts = path.split('/')
    return '/'.join(parts[:2]) if len(parts) > 1 else path


def _acceptable_table(allowlisted, styles) -> Table:
    """One row per allowlisted file with its justification — the files that
    intentionally keep .json I/O and are NOT migrating to the database."""
    reasons = {}
    for a in allowlisted:
        reasons.setdefault(a['file'], a.get('reason', ''))
    rows = [[Paragraph('<b>File</b>', styles['tbl_hdr']),
             Paragraph('<b>Why it stays a file (not migrating)</b>',
                       styles['tbl_hdr'])]]
    for fp in sorted(reasons, key=lambda p: (_area(p), p)):
        rows.append([Paragraph(fp, styles['tbl_cell']),
                     Paragraph(reasons[fp], styles['tbl_cell'])])
    t = Table(rows, colWidths=[70 * mm, 90 * mm], repeatRows=1)
    style = TableStyle(_TABLE_STYLE.getCommands())
    style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
    t.setStyle(style)
    return t


def _by_area_table(io_files, styles) -> Table:
    counts = Counter(_area(f) for f in io_files)
    rows = [[Paragraph('<b>Area</b>', styles['tbl_hdr']),
             Paragraph('<b>I/O files</b>', styles['tbl_hdr'])]]
    for area, n in counts.most_common():
        rows.append([Paragraph(area, styles['tbl_cell']),
                     Paragraph(str(n), styles['tbl_cell_r'])])
    t = Table(rows, colWidths=[130 * mm, 30 * mm])
    t.setStyle(_TABLE_STYLE)
    return t


def _per_file_table(io_findings, styles) -> Table:
    per = defaultdict(Counter)
    for f in io_findings:
        per[f['file']][f['kind']] += 1
    rows = [[Paragraph('<b>File</b>', styles['tbl_hdr']),
             Paragraph('<b>Load</b>', styles['tbl_hdr']),
             Paragraph('<b>Create / update</b>', styles['tbl_hdr'])]]
    for fp in sorted(per, key=lambda p: (_area(p), -(per[p]['read'] + per[p]['write']))):
        c = per[fp]
        rows.append([
            Paragraph(fp, styles['tbl_cell']),
            Paragraph(str(c['read']), styles['tbl_cell_r']),
            Paragraph(str(c['write']), styles['tbl_cell_r']),
        ])
    t = Table(rows, colWidths=[120 * mm, 20 * mm, 30 * mm], repeatRows=1)
    t.setStyle(_TABLE_STYLE)
    return t


def create_pdf_report(scan: dict, output_path, root, generated: str):
    """Assemble the standalone json-file audit PDF from a ``scan_repo`` result."""
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=24 * mm, bottomMargin=14 * mm,
    )
    S = _styles()
    story = []

    # --- cover -------------------------------------------------------------
    story.append(Paragraph('JSON-File Audit Report', S['cover_title']))
    story.append(Paragraph(
        'Zero-Tolerance Tracker — .json loads &amp; create/updates outside the '
        'database seam: what needs to migrate vs. what is acceptable to keep',
        S['cover_sub']))
    story.append(Spacer(1, 4 * mm))

    n_io = len(scan['io_files'])
    n_accept = len({a['file'] for a in scan['allowlisted']})
    mode = 'GATING (zero-tolerance)' if GATED else 'TRACKING (non-gating)'
    mode_colour = RED if (GATED and scan['io_findings']) else GREEN
    story.append(Paragraph(
        f"<b>Generated:</b> {generated}<br/>"
        f"<b>Project root:</b> {root}<br/>"
        f"<b>Policy:</b> no module loads, creates, or updates a .json file on "
        f"disk — all such state lives in PostgreSQL behind src/database.<br/>"
        f"<b>Scope:</b> all first-party .py except tests/, docs/models, "
        f"src/routes/governance, src/models, and inert dirs.<br/>"
        f"<b>Acceptable (allowlisted, not migrating):</b> {n_accept} file(s) — "
        f"config exports, analytical-model artifacts, provenance metadata, test "
        f"harness, and standalone tools, each with a recorded justification.<br/>"
        f"<b>Mode:</b> <font color='{mode_colour.hexval()}'>{mode}</font>",
        S['cover_meta']))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width='100%', thickness=1.2, color=NAVY))
    story.append(Spacer(1, 3 * mm))

    # --- headline metrics --------------------------------------------------
    story.append(Paragraph(
        f"<b>{scan['scanned']}</b> files scanned &nbsp;·&nbsp; "
        f"<b>{n_io}</b> needs-migration files &nbsp;·&nbsp; "
        f"<b>{scan['reads']}</b> load &nbsp;·&nbsp; "
        f"<b>{scan['writes']}</b> create/update &nbsp;·&nbsp; "
        f"<b>{n_accept}</b> acceptable (allowlisted) &nbsp;·&nbsp; "
        f"<b>{scan['refs']}</b> bare path reference(s)", S['body']))
    story.append(Spacer(1, 4 * mm))

    # --- needs migration: backlog by area ----------------------------------
    story.append(Paragraph('Needs migration — backlog by area', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        'Live port state still loaded or created/updated as a .json file outside '
        'the database seam. These shrink to zero as each artifact moves onto the '
        'seam, at which point the audit flips to a zero-tolerance gate.', S['body']))
    story.append(Spacer(1, 2 * mm))
    if scan['io_files']:
        story.append(_by_area_table(scan['io_files'], S))
    else:
        story.append(Paragraph('No .json I/O outside the seam — backlog clear.',
                               S['body']))
    story.append(PageBreak())

    # --- needs migration: per-file detail (complete list) ------------------
    story.append(Paragraph('Needs migration — per-file detail '
                           '(every load &amp; create/update)', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    if scan['io_findings']:
        story.append(_per_file_table(scan['io_findings'], S))
    else:
        story.append(Paragraph('None.', S['body']))

    # --- acceptable: allowlisted files, intentionally not migrating --------
    story.append(PageBreak())
    story.append(Paragraph('Acceptable — intentionally not migrating '
                           '(allowlisted)', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        'Files whose .json I/O is deliberate and exempt from the migration — '
        'config exports whose canonical values live in config.port, analytical-'
        'model artifacts, BCBS 239 provenance metadata, the test/audit harness, '
        'and standalone developer tools. Each is registered with a justification; '
        'a contract test removes any entry that no longer touches a .json file, so '
        'this list cannot accumulate stale exemptions.', S['body']))
    story.append(Spacer(1, 2 * mm))
    if scan['allowlisted']:
        story.append(_acceptable_table(scan['allowlisted'], S))
    else:
        story.append(Paragraph('None.', S['body']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path
