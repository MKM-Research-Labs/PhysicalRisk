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

"""Subsection 4.2: copyright/license-header governance audit.

Sits next to the coverage (Section 3) and __init__.py (Subsection 4.1) audits.
The heavy scan/repair logic lives in the standalone ``docs.models.copyright_headers``
module (run in the Phase-4 audit loop, which repairs headers in place and writes
``copyright_headers_record.json``); this builder reports current compliance plus
what was replaced.
"""

import json

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .._constants import NAVY, _TBL_STYLE_BASE, AUDIT_DIR, _root


def _build_copyright_headers(styles) -> list:
    """Flag any .py/.js file whose header is not the canonical 19-line MKM
    license header from docs/shared/copyright.py.  The audit is self-healing:
    the standalone module rewrites non-compliant headers, so in steady state
    this subsection reports PASS."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.2 Copyright Header Audit', styles['h3']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Policy: every first-party <b>.py</b> and <b>.js</b> file must begin '
        'with the exact 19-line MKM Research Labs license header defined in '
        '<b>docs/shared/copyright.py</b> (after an optional shebang). The audit '
        'is self-healing — a wrong or missing header is rewritten in place and '
        'recorded as (a) wrong, (b) replaced, (c) now compatible.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    # Read-only (dry) scan for current compliance — mirrors how 4.1 re-runs its
    # analysis live rather than depending on a report file.
    try:
        from docs.models.copyright_headers import fix_repo
        scan = fix_repo(_root, apply=False)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run copyright-header audit: {exc}', styles['body']))
        return elems

    scanned = scan['scanned']
    compliant = scan['already_compliant']
    remaining = scan['remaining']

    # Files repaired on record (written by the standalone module's run earlier
    # in the audit loop / by the pytest self-heal).
    fixed = []
    try:
        rec = json.loads(
            (AUDIT_DIR / 'copyright_headers_record.json').read_text(encoding='utf-8'))
        fixed = rec.get('fixed', [])
    except (OSError, ValueError):
        fixed = []

    elems.append(Paragraph(
        f'Files scanned: <b>{scanned}</b> &nbsp;|&nbsp; '
        f'Compliant: <b>{compliant}</b> &nbsp;|&nbsp; '
        f'Headers replaced (on record): <b>{len(fixed)}</b> &nbsp;|&nbsp; '
        f'Still non-compliant: <b>{len(remaining)}</b>.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not remaining:
        elems.append(Paragraph(
            'Every scanned .py/.js file carries the canonical header. '
            '<b>PASS</b>', styles['body']))
    else:
        elems.append(Paragraph(
            f'{len(remaining)} file(s) are not yet compliant (showing up to 25). '
            'Run <b>python -m docs.models.copyright_headers</b> to repair.',
            styles['body']))
        elems.append(Spacer(1, 2 * mm))
        data = [[
            Paragraph('<b>File (relative to project root)</b>', styles['tbl_hdr']),
            Paragraph('<b>Existing header (first line)</b>', styles['tbl_hdr']),
        ]]
        for r in remaining[:25]:
            rel = r['file']
            if len(rel) > 58:
                rel = '…' + rel[-56:]
            old_lines = (r.get('old_header') or '').splitlines()
            old0 = old_lines[0] if old_lines else '(no header present)'
            if len(old0) > 58:
                old0 = old0[:56] + '…'
            data.append([
                Paragraph(rel, styles['tbl_cell']),
                Paragraph(old0, styles['tbl_cell']),
            ])
        tbl = Table(data, colWidths=[96 * mm, 72 * mm])
        tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
        ]))
        elems.append(tbl)

    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Full per-file remediation — (a) wrong → (b) replaced → (c) compatible '
        '— in the standalone <b>copyright_headers_report.pdf</b> / '
        '<b>copyright_headers_record.json</b> under data/output/audit/.',
        styles['body']))
    return elems
