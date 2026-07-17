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

"""Render the database-usage audit (4.6 scan) into a standalone PDF.

Reuses the 4.6 scanner and the full-audit styling so the standalone report and
the consolidated audit stay visually and numerically identical."""

from collections import Counter

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from docs.models.full_audit._constants import NAVY, GREEN, GREY

_ROW_ALT = HexColor('#F4F6FA')

_TABLE_STYLE = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
    ('TEXTCOLOR', (0, 0), (-1, 0), GREY),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.4, GREY),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, _ROW_ALT]),
    ('TOPPADDING', (0, 0), (-1, -1), 2),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
])


def _styled(extra=None):
    style = TableStyle(_TABLE_STYLE.getCommands())
    for cmd in (extra or []):
        style.add(*cmd)
    return style


def _area(path: str) -> str:
    parts = path.split('/')
    return '/'.join(parts[:2]) if len(parts) > 1 else path


def _by_area_table(caller_files, styles) -> Table:
    counts = Counter(_area(f) for f in caller_files)
    rows = [[Paragraph('<b>Area</b>', styles['tbl_hdr']),
             Paragraph('<b>Modules calling the seam</b>', styles['tbl_hdr'])]]
    for area, n in counts.most_common():
        rows.append([Paragraph(area, styles['tbl_cell']),
                     Paragraph(str(n), styles['tbl_cell_r'])])
    t = Table(rows, colWidths=[130 * mm, 30 * mm])
    t.setStyle(_TABLE_STYLE)
    return t


def _adopters_table(by_file, styles) -> Table:
    """Every seam caller mapped to the exact database functions it calls."""
    rows = [[Paragraph('<b>Module</b>', styles['tbl_hdr']),
             Paragraph('<b>#</b>', styles['tbl_hdr']),
             Paragraph('<b>Database functions called</b>', styles['tbl_hdr'])]]
    for fp in sorted(by_file, key=lambda p: (_area(p), p)):
        funcs = by_file[fp]
        rows.append([
            Paragraph(fp, styles['tbl_cell']),
            Paragraph(str(len(funcs)), styles['tbl_cell_r']),
            Paragraph(', '.join(funcs), styles['tbl_cell']),
        ])
    t = Table(rows, colWidths=[62 * mm, 8 * mm, 90 * mm], repeatRows=1)
    t.setStyle(_styled([('ALIGN', (1, 1), (1, -1), 'CENTER')]))
    return t


def _coverage_table(by_func, styles) -> Table:
    """Each exercised public function and how many modules call it."""
    rows = [[Paragraph('<b>Database function (used)</b>', styles['tbl_hdr']),
             Paragraph('<b>Caller modules</b>', styles['tbl_hdr'])]]
    for fn in sorted(by_func, key=lambda k: (-len(by_func[k]), k)):
        rows.append([Paragraph(fn, styles['tbl_cell']),
                     Paragraph(str(len(by_func[fn])), styles['tbl_cell_r'])])
    t = Table(rows, colWidths=[130 * mm, 30 * mm], repeatRows=1)
    t.setStyle(_styled([('ALIGN', (1, 1), (1, -1), 'CENTER')]))
    return t


def create_pdf_report(scan: dict, output_path, root, generated: str):
    """Assemble the standalone database-usage PDF from a ``scan_repo`` result."""
    from docs.models.full_audit.styles import _styles
    from docs.models.full_audit.helpers import _header_footer

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=24 * mm, bottomMargin=14 * mm,
    )
    S = _styles()
    story = []

    n_callers = len(scan['caller_files'])
    n_api = len(scan['api_names'])
    n_used = len(scan['used_funcs'])
    n_unused = len(scan['unused_funcs'])

    # --- cover -------------------------------------------------------------
    story.append(Paragraph('Database-Usage Audit Report', S['cover_title']))
    story.append(Paragraph(
        'Complete map of database-seam adoption — every module that calls the '
        'database, the exact functions it calls, and the modules still on .json',
        S['cover_sub']))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        f"<b>Generated:</b> {generated}<br/>"
        f"<b>Project root:</b> {root}<br/>"
        f"<b>Policy:</b> all persisted/queried state goes through the one "
        f"<b>database</b> package (src/database); this report is the positive "
        f"map of who calls it and how, the sibling to the 4.4 no-raw-DB-access "
        f"gate and the 4.5 no-.json gate.<br/>"
        f"<b>Scope:</b> all first-party .py except tests/ and inert dirs, and "
        f"except src/database itself (the seam defines the API). Includes "
        f"src/models and docs/models.<br/>"
        f"<b>Mode:</b> <font color='{GREEN.hexval()}'>MAP (informational)</font>",
        S['cover_meta']))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width='100%', thickness=1.2, color=NAVY))
    story.append(Spacer(1, 3 * mm))

    # --- headline metrics --------------------------------------------------
    story.append(Paragraph(
        f"<b>{scan['scanned']}</b> files scanned &nbsp;·&nbsp; "
        f"<b>{n_callers}</b> seam callers &nbsp;·&nbsp; "
        f"<b>{len(scan['calls'])}</b> call sites &nbsp;·&nbsp; "
        f"<b>{n_used}/{n_api}</b> public functions used &nbsp;·&nbsp; "
        f"<b>{n_unused}</b> never called &nbsp;·&nbsp; "
        f"<b>{len(scan['json_io_files'])}</b> still on .json &nbsp;·&nbsp; "
        f"<b>{len(scan['both_files'])}</b> do both", S['body']))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph('Seam callers by area', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(_by_area_table(scan['caller_files'], S))
    story.append(PageBreak())

    # --- section A: adopters (file -> functions) ---------------------------
    story.append(Paragraph('A — Seam adopters: every module mapped to the '
                           'database functions it calls', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    if scan['by_file']:
        story.append(_adopters_table(scan['by_file'], S))
    else:
        story.append(Paragraph('No first-party module calls the seam.', S['body']))
    story.append(PageBreak())

    # --- section B: API coverage -------------------------------------------
    story.append(Paragraph('B — API coverage: public functions and how many '
                           'modules call each', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f'{n_used} of {n_api} public symbols are exercised by first-party code. '
        f'The {n_unused} below are <b>never called outside the seam and tests</b> '
        f'— dead API, internal-only helpers, or surface reserved for future/tooling '
        f'use; each is worth a deliberate keep-or-remove decision.', S['body']))
    story.append(Spacer(1, 2 * mm))
    story.append(_coverage_table(scan['by_func'], S))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        f'<b>Never called by first-party code ({n_unused}):</b> '
        f'{", ".join(scan["unused_funcs"]) or "none — full coverage"}.', S['body']))
    story.append(PageBreak())

    # --- section C: complement (still on .json) ----------------------------
    story.append(Paragraph('C — Not on the seam: modules still using .json '
                           '(the 4.5 backlog, verbatim)', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f'These <b>{len(scan["json_io_files"])}</b> module(s) load or create/update '
        f'a .json file directly ({scan["json_reads"]} load, {scan["json_writes"]} '
        f'create/update) rather than going through the seam — the live migration '
        f'backlog. See the JSON-File Audit for per-line detail.', S['body']))
    story.append(Spacer(1, 2 * mm))
    if scan['json_io_files']:
        for f in scan['json_io_files']:
            tag = '  (also calls the seam — mid-migration)' if f in scan['both_files'] else ''
            story.append(Paragraph(f'• {f}{tag}', S['body']))
    else:
        story.append(Paragraph('None — all persisted state is on the seam.',
                               S['body']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path
