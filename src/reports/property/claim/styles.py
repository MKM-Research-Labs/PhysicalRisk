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

"""Paragraph styles used across all claim report pages."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import TableStyle
from reports.theme_pdf import pdf_colour

# ── Shared TableStyle constants ──────────────────────────────────────────────
# Purple header with alternating lavender rows — used by page3 (sequence-level
# assessment) and page4 (sequence-level LTV).

PURPLE_TABLE_STYLE = TableStyle([
    ('BACKGROUND',     (0, 0), (-1, 0),  pdf_colour('purple-dark')),
    ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
    ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
    ('FONTSIZE',       (0, 0), (-1, -1), 8),
    ('ALIGN',          (2, 1), (-1, -1), 'CENTER'),
    ('GRID',           (0, 0), (-1, -1), 0.4, pdf_colour('blue-grey-mist')),
    ('BOX',            (0, 0), (-1, -1), 1,   pdf_colour('purple-dark')),
    ('TOPPADDING',     (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
    ('LEFTPADDING',    (0, 0), (-1, -1), 4),
    ('RIGHTPADDING',   (0, 0), (-1, -1), 4),
    ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
     [colors.white, pdf_colour('purple-bg')]),
])


def setup_styles():
    """Build and return the full set of paragraph styles for claim reports."""
    base = getSampleStyleSheet()

    def _add(name, **kw):
        if name not in base:
            base.add(ParagraphStyle(name=name, **kw))

    _add('ClaimTitle',
         parent=base['Normal'],
         fontSize=22,
         fontName='Helvetica-Bold',
         textColor=pdf_colour('navy'),
         alignment=TA_CENTER,
         spaceAfter=6)

    _add('ClaimSubTitle',
         parent=base['Normal'],
         fontSize=14,
         fontName='Helvetica',
         textColor=pdf_colour('navy-mid'),
         alignment=TA_CENTER,
         spaceAfter=10)

    _add('ClaimRefBanner',
         parent=base['Normal'],
         fontSize=13,
         fontName='Helvetica-Bold',
         textColor=colors.white,
         alignment=TA_CENTER,
         spaceAfter=14)

    _add('SectionHeader',
         parent=base['Normal'],
         fontSize=13,
         fontName='Helvetica-Bold',
         textColor=pdf_colour('navy'),
         spaceBefore=10,
         spaceAfter=4)

    _add('SubSectionHeader',
         parent=base['Normal'],
         fontSize=11,
         fontName='Helvetica-Bold',
         textColor=pdf_colour('green-deep'),
         spaceBefore=8,
         spaceAfter=3)

    _add('BodyText10',
         parent=base['Normal'],
         fontSize=10,
         leading=14)

    _add('BodyText9',
         parent=base['Normal'],
         fontSize=9,
         leading=12)

    _add('NoteBox',
         parent=base['Normal'],
         fontSize=9,
         leading=13,
         textColor=pdf_colour('purple-dark'))

    _add('Disclaimer',
         parent=base['Normal'],
         fontSize=8,
         leading=11,
         textColor=colors.grey,
         fontName='Helvetica-Oblique')

    _add('FooterNote',
         parent=base['Normal'],
         fontSize=8,
         leading=10,
         textColor=pdf_colour('blue-grey-dark'),
         alignment=TA_CENTER)

    _add('SignatureLine',
         parent=base['Normal'],
         fontSize=9,
         leading=13,
         textColor=pdf_colour('log-bg'))

    _add('StatsBar',
         parent=base['Normal'],
         fontSize=9,
         fontName='Helvetica-Bold',
         textColor=pdf_colour('slate-dark'),
         alignment=TA_CENTER)

    return base
