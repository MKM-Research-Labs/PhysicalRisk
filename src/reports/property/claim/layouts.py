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

"""Shared layout helpers: table cell styles and page header/footer callback."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle

from .constants import MARGIN, PAGE_H, PAGE_W
from reports.theme_pdf import pdf_colour


def white_hdr_style(styles) -> ParagraphStyle:
    """Paragraph style for navy-background table column headers (white bold text)."""
    return ParagraphStyle(
        'WhiteHdr',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        textColor=colors.white,
        alignment=TA_CENTER,
    )


def body_style(styles, font: str = 'Helvetica', align: int = TA_LEFT) -> ParagraphStyle:
    """Paragraph style for table body cells."""
    return ParagraphStyle(
        'BodyCell',
        parent=styles['Normal'],
        fontSize=8,
        fontName=font,
        alignment=align,
    )


def build_header_footer(claim_ref: str):
    """Return a canvas callback that draws the page header and footer.

    The returned function is suitable for use as both ``onFirstPage`` and
    ``onLaterPages`` arguments to ``SimpleDocTemplate.build()``.
    """
    def _header_footer(canvas, doc):
        canvas.saveState()
        page_num = canvas.getPageNumber()

        # ---- Header ----
        y_hdr = PAGE_H - 0.55 * MARGIN / 0.75
        y_hdr = PAGE_H - 0.55 * 72  # 0.55 inch in points
        canvas.setStrokeColor(pdf_colour('navy'))
        canvas.setLineWidth(1.2)
        canvas.line(MARGIN, y_hdr, PAGE_W - MARGIN, y_hdr)

        canvas.setFont('Helvetica-Bold', 7.5)
        canvas.setFillColor(pdf_colour('navy'))
        canvas.drawString(
            MARGIN, y_hdr + 4,
            'MKM Research Labs \u2014 Flood Damage Assessment Report'
        )
        canvas.drawRightString(
            PAGE_W - MARGIN, y_hdr + 4,
            f'Claim Ref: {claim_ref}'
        )

        # ---- Footer ----
        y_ftr = 0.45 * 72  # 0.45 inch in points
        canvas.setStrokeColor(pdf_colour('blue-grey-pale'))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y_ftr + 8, PAGE_W - MARGIN, y_ftr + 8)

        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(pdf_colour('blue-grey-dark'))
        canvas.drawCentredString(
            PAGE_W / 2, y_ftr,
            f'CONFIDENTIAL  |  Claim Ref: {claim_ref}  |  Page {page_num}'
        )
        canvas.restoreState()

    return _header_footer
