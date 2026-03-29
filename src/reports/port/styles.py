# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""Styles, colours, and table helpers for the portfolio report."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Table, TableStyle

# ---- Colours ----
BLUE = colors.HexColor('#1565C0')
DARK_BLUE = colors.darkblue
LIGHT_BLUE = colors.HexColor('#E3F2FD')
LIGHT_GREEN = colors.HexColor('#E8F5E9')
LIGHT_AMBER = colors.HexColor('#FFF8E1')
LIGHT_RED = colors.HexColor('#FFEBEE')
GREY = colors.HexColor('#757575')

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
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#BDBDBD')),
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
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#E0E0E0')),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
        ]))
        return t
