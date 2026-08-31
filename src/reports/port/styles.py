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

"""Styles, colours, and table helpers for the portfolio report."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle
from reports.theme_pdf import pdf_colour

# ---- Colours ----
BLUE = pdf_colour('accent-mid')
DARK_BLUE = colors.darkblue
LIGHT_BLUE = pdf_colour('accent-soft')
LIGHT_GREEN = pdf_colour('ok-bg')
LIGHT_AMBER = pdf_colour('warn-bg')
LIGHT_RED = pdf_colour('danger-bg-soft')
GREY = pdf_colour('text-4')

# ---- Reusable table style ----
HDR_STYLE = [
    ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 8),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
    ('TOPPADDING', (0, 0), (-1, 0), 5),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 7),
    ('TOPPADDING', (0, 1), (-1, -1), 2),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.4, pdf_colour('faint')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
]

ALT_ROWS_BLUE = [('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BLUE, colors.white])]
ALT_ROWS_GREEN = [('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREEN, colors.white])]
ALT_ROWS_AMBER = [('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_AMBER, colors.white])]

AVAIL_WIDTH = 7.3 * inch  # 8.5 - 1.2 margins


class StylesMixin:
    """Mixin providing paragraph styles and table builders."""

    def _setup_styles(self):
        self.title_style = ParagraphStyle(
            'PortTitle', parent=self._styles['Heading1'],
            fontSize=18, alignment=TA_CENTER, spaceAfter=4,
            textColor=DARK_BLUE, fontName='Helvetica-Bold',
        )
        self.subtitle_style = ParagraphStyle(
            'PortSubtitle', parent=self._styles['Normal'],
            fontSize=10, alignment=TA_CENTER, spaceAfter=12,
            textColor=GREY, fontName='Helvetica',
        )
        self.section_style = ParagraphStyle(
            'PortSection', parent=self._styles['Heading2'],
            fontSize=13, textColor=DARK_BLUE, spaceBefore=14, spaceAfter=6,
            fontName='Helvetica-Bold',
        )
        self.subsection_style = ParagraphStyle(
            'PortSubsection', parent=self._styles['Heading3'],
            fontSize=10, textColor=BLUE, spaceBefore=8, spaceAfter=4,
            fontName='Helvetica-Bold',
        )
        self.body_style = ParagraphStyle(
            'PortBody', parent=self._styles['Normal'],
            fontSize=9, textColor=colors.black, spaceAfter=4,
        )
        self.kv_style = ParagraphStyle(
            'PortKV', parent=self._styles['Normal'],
            fontSize=9, textColor=colors.black, leftIndent=12, spaceAfter=2,
        )

    def _make_table(self, header, rows, col_widths=None, alt_color=None):
        """Build a styled Table from header + rows."""
        all_rows = [header] + rows
        style_cmds = list(HDR_STYLE)
        if alt_color:
            style_cmds.extend(alt_color)
        else:
            style_cmds.extend(ALT_ROWS_BLUE)
        t = Table(all_rows, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle(style_cmds))
        return t

    def _kv_table(self, pairs, label_width=2.8*inch):
        """Build a two-column key-value table."""
        val_width = AVAIL_WIDTH - label_width
        rows = [[Paragraph(f'<b>{k}</b>', self.body_style),
                 Paragraph(str(v), self.body_style)] for k, v in pairs]
        t = Table(rows, colWidths=[label_width, val_width])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, pdf_colour('line')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, pdf_colour('raised')]),
        ]))
        return t
