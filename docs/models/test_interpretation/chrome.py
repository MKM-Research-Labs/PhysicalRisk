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

"""Running header/footer for the assessment PDF.

Kept separate from the content builders so ``builder.py`` stays within the
file-size limit, and because page chrome is a distinct concern from the sections.
"""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from ..full_audit._constants import NAVY, STEEL

# This is a sibling of the full audit, not the full audit itself, so it must not
# reuse full_audit's "Full Audit Report" header.
_HEADER_LABEL = "Test Interpretation — Assessment"


def _header_footer(canvas, doc):
    """Assessment-specific running header/footer (mirrors full_audit's styling
    with the correct document label)."""
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 20 * mm, w, 20 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(20 * mm, h - 12 * mm, "MKM Physical Risk Platform")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        w - 20 * mm, h - 12 * mm,
        f'{_HEADER_LABEL}  |  {datetime.now().strftime("%d %B %Y")}')
    canvas.setFillColor(STEEL)
    canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(
        20 * mm, 2.5 * mm,
        "CONFIDENTIAL — MKM Research Labs  |  SR 11-7 / SS1/23 Model Governance")
    canvas.drawRightString(w - 20 * mm, 2.5 * mm, f"Page {doc.page}")
    canvas.restoreState()
