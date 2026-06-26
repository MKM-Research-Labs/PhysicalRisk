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
        'database seam', S['cover_sub']))
    story.append(Spacer(1, 4 * mm))

    n_io = len(scan['io_files'])
    mode = 'GATING (zero-tolerance)' if GATED else 'TRACKING (non-gating)'
    mode_colour = RED if (GATED and scan['io_findings']) else GREEN
    story.append(Paragraph(
        f"<b>Generated:</b> {generated}<br/>"
        f"<b>Project root:</b> {root}<br/>"
        f"<b>Policy:</b> no module loads, creates, or updates a .json file on "
        f"disk — all such state lives in PostgreSQL behind src/database.<br/>"
        f"<b>Scope:</b> all first-party .py except tests/, docs/models, "
        f"src/routes/governance, src/models, and inert dirs.<br/>"
        f"<b>Mode:</b> <font color='{mode_colour.hexval()}'>{mode}</font>",
        S['cover_meta']))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width='100%', thickness=1.2, color=NAVY))
    story.append(Spacer(1, 3 * mm))

    # --- headline metrics --------------------------------------------------
    story.append(Paragraph(
        f"<b>{scan['scanned']}</b> files scanned &nbsp;·&nbsp; "
        f"<b>{n_io}</b> I/O backlog files &nbsp;·&nbsp; "
        f"<b>{scan['reads']}</b> load &nbsp;·&nbsp; "
        f"<b>{scan['writes']}</b> create/update &nbsp;·&nbsp; "
        f"<b>{scan['refs']}</b> bare path reference(s)", S['body']))
    story.append(Spacer(1, 4 * mm))

    # --- backlog by area ---------------------------------------------------
    story.append(Paragraph('Backlog by area', S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    if scan['io_files']:
        story.append(_by_area_table(scan['io_files'], S))
    else:
        story.append(Paragraph('No .json I/O outside the seam — backlog clear.',
                               S['body']))
    story.append(PageBreak())

    # --- per-file detail (complete list) -----------------------------------
    story.append(Paragraph('Per-file detail — every load &amp; create/update',
                           S['h3']))
    story.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    story.append(Spacer(1, 2 * mm))
    if scan['io_findings']:
        story.append(_per_file_table(scan['io_findings'], S))
    else:
        story.append(Paragraph('None.', S['body']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path
