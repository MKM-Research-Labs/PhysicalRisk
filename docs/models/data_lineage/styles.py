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

"""Paragraph styles, table styles, and status helpers for the lineage report."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Spacer, TableStyle

from ._constants import NAVY, STEEL, GREEN, AMBER, RED
from reports.theme_pdf import pdf_colour


def _styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('DLTitle', parent=base['Heading1'],
                                fontSize=22, textColor=NAVY,
                                spaceAfter=8, alignment=TA_CENTER,
                                fontName='Helvetica-Bold'),
        'subtitle': ParagraphStyle('DLSub', parent=base['Normal'],
                                   fontSize=12, textColor=STEEL,
                                   spaceAfter=4, alignment=TA_CENTER),
        'meta': ParagraphStyle('DLMeta', parent=base['Normal'],
                               fontSize=9, textColor=pdf_colour('blue-grey-dark'),
                               alignment=TA_CENTER, spaceAfter=2),
        'h2': ParagraphStyle('DLH2', parent=base['Heading2'],
                              fontSize=14, textColor=NAVY,
                              spaceBefore=14, spaceAfter=6,
                              fontName='Helvetica-Bold'),
        'h3': ParagraphStyle('DLH3', parent=base['Heading3'],
                              fontSize=11, textColor=STEEL,
                              spaceBefore=8, spaceAfter=4,
                              fontName='Helvetica-Bold'),
        'body': ParagraphStyle('DLBody', parent=base['BodyText'],
                               fontSize=9, leading=13),
        'small': ParagraphStyle('DLSmall', parent=base['Normal'],
                                fontSize=7.5, textColor=pdf_colour('blue-grey-light'),
                                leading=11),
        'code': ParagraphStyle('DLCode', parent=base['Code'],
                               fontSize=8, leading=11,
                               textColor=pdf_colour('text')),
        'note': ParagraphStyle('DLNote', parent=base['BodyText'],
                               fontSize=8, leading=11,
                               textColor=pdf_colour('text-3'),
                               leftIndent=12),
    }


def _header_style():
    return TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',      (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, 0), 8.5),
        ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING',  (0, 0), (-1, 0), 8),
        ('BACKGROUND',     (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, pdf_colour('header-from')]),
        ('FONTNAME',       (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 1), (-1, -1), 8),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',           (0, 0), (-1, -1), 0.4, pdf_colour('divider')),
        ('TOPPADDING',     (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING',  (0, 1), (-1, -1), 4),
    ])


def _section_rule(story):
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=1,
                             color=pdf_colour('silver')))
    story.append(Spacer(1, 0.1 * inch))


def _status_colour(status: str):
    return {'fresh': GREEN, 'stale': AMBER, 'missing': RED}.get(status, STEEL)


def _status_label(status: str) -> str:
    return {'fresh': 'FRESH', 'stale': 'STALE', 'missing': 'MISSING'}.get(
        status, status.upper())
