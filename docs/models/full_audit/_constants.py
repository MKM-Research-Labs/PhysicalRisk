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

"""Paths, colours, and the base table style for the full audit report."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / 'src'))

try:
    from reportlab.lib import colors

    # The token resolver imports reportlab as well, so it belongs inside the same
    # guard: without reportlab neither is importable, and one clear message beats two.
    from reports.theme_pdf import pdf_colour
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

from config import config
AUDIT_DIR = config.get_reports_dir('audit')
SRC_DIR = _root / 'src'
OUTPUT_PDF = AUDIT_DIR / 'full_audit_report.pdf'

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

# The nine names 21 audit modules import. They were a private palette — nine colours
# written down here and nowhere else, which is exactly the thing §4.8 exists to find —
# and are now resolved from config/theme. The names stay, because they are the audit's
# own vocabulary and every importer reads better for them; only the values move.
NAVY = pdf_colour('navy')
STEEL = pdf_colour('slate-dark')
BLUE = pdf_colour('accent-mid')
LIGHT_BG = pdf_colour('sunken')
HEADER_BG = pdf_colour('info-bg')
GREEN = pdf_colour('green-dark')
AMBER = pdf_colour('amber-deep')
RED = pdf_colour('red-deep')
GREY = pdf_colour('blue-grey-pale')

# ---------------------------------------------------------------------------
# Base table style — shared by all section tables
# ---------------------------------------------------------------------------

_TBL_STYLE_BASE = [
    ('FONTSIZE',       (0, 0), (-1, 0),  8.5),
    ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
    ('BACKGROUND',     (0, 0), (-1, 0),  NAVY),
    ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ('GRID',           (0, 0), (-1, -1), 0.4, pdf_colour('blue-grey-haze')),
    ('BOX',            (0, 0), (-1, -1), 1.0, STEEL),
    ('FONTSIZE',       (0, 1), (-1, -1), 8),
    ('TOPPADDING',     (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
    ('LEFTPADDING',    (0, 0), (-1, -1), 6),
    ('RIGHTPADDING',   (0, 0), (-1, -1), 6),
    ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
]
