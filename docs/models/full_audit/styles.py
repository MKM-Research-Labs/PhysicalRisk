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

"""Paragraph style sheet for the full audit report."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from ._constants import NAVY, STEEL
from reports.theme_pdf import pdf_colour


def _styles():
    base = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle(
            'FATitle', parent=base['Heading1'],
            fontSize=26, textColor=NAVY, spaceAfter=8,
            alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'cover_sub': ParagraphStyle(
            'FASub', parent=base['Normal'],
            fontSize=13, textColor=STEEL, spaceAfter=4,
            alignment=TA_CENTER),
        'cover_meta': ParagraphStyle(
            'FAMeta', parent=base['Normal'],
            fontSize=9, textColor=pdf_colour('blue-grey-dark'),
            alignment=TA_CENTER, spaceAfter=2),
        'h2': ParagraphStyle(
            'FAH2', parent=base['Heading2'],
            fontSize=13, textColor=NAVY,
            spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'),
        'h3': ParagraphStyle(
            'FAH3', parent=base['Heading3'],
            fontSize=10, textColor=STEEL,
            spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'),
        'body': ParagraphStyle(
            'FABody', parent=base['BodyText'],
            fontSize=9, leading=13),
        'small': ParagraphStyle(
            'FASmall', parent=base['Normal'],
            fontSize=7.5, textColor=pdf_colour('blue-grey-light'), leading=11),
        'tbl_hdr': ParagraphStyle(
            'FATHdr', parent=base['Normal'],
            fontSize=8.5, textColor=colors.white, fontName='Helvetica-Bold'),
        'tbl_cell': ParagraphStyle(
            'FATCell', parent=base['Normal'],
            fontSize=8, leading=11),
        'tbl_cell_r': ParagraphStyle(
            'FATCellR', parent=base['Normal'],
            fontSize=8, leading=11, alignment=TA_RIGHT),
        'metric_val': ParagraphStyle(
            'FAMetricV', parent=base['Normal'],
            fontSize=20, textColor=NAVY, fontName='Helvetica-Bold',
            alignment=TA_CENTER),
        'metric_lbl': ParagraphStyle(
            'FAMetricL', parent=base['Normal'],
            fontSize=8, textColor=STEEL, alignment=TA_CENTER),
    }
