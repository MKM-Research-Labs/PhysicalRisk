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

"""Shared styles and severity helpers for the hard-coding audit PDF."""

import sys
from pathlib import Path
# These generators run as `python -m docs.models.<pkg>`, which does NOT put src/
# on sys.path, so the shared token resolver is not importable without this.
# Same bootstrap as full_audit/_constants.py and data_lineage/_constants.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))

from reports.theme_pdf import pdf_colour

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Spacer, TableStyle
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)


def _risk_colour(count: int):
    if count == 0:
        return pdf_colour('marker-green')   # green
    if count <= 5:
        return pdf_colour('marker-amber')   # amber
    return pdf_colour('marker-red')       # red


def _risk_label(count: int) -> str:
    if count == 0:
        return 'COMPLIANT'
    if count <= 5:
        return 'REVIEW'
    return 'ACTION REQUIRED'


def _styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('HCTitle', parent=base['Heading1'],
                                fontSize=22, textColor=pdf_colour('near-black'),
                                spaceAfter=20, alignment=TA_CENTER),
        'h2': ParagraphStyle('HCH2', parent=base['Heading2'],
                              fontSize=14, textColor=pdf_colour('slate-ink'),
                              spaceAfter=8, spaceBefore=14),
        'h3': ParagraphStyle('HCH3', parent=base['Heading3'],
                              fontSize=11, textColor=pdf_colour('marker-slate'),
                              spaceAfter=6, spaceBefore=10),
        'body': ParagraphStyle('HCBody', parent=base['BodyText'],
                               fontSize=9, leading=13),
        'code': ParagraphStyle('HCCode', parent=base['Code'],
                               fontSize=8, leading=11,
                               textColor=pdf_colour('text')),
        'note': ParagraphStyle('HCNote', parent=base['BodyText'],
                               fontSize=8, leading=11,
                               textColor=pdf_colour('text-3'),
                               leftIndent=12),
    }


def _header_style():
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), pdf_colour('slate-ink')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND',    (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, pdf_colour('header-from')]),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.4, pdf_colour('divider')),
        ('TOPPADDING',    (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ])


def _severity_badge_colour(label: str):
    return {
        'HIGH':   pdf_colour('marker-red'),
        'MEDIUM': pdf_colour('marker-orange'),
        'LOW':    pdf_colour('marker-green'),
        'INFO':   pdf_colour('marker-blue'),
    }.get(label, colors.grey)


def _section_rule(story):
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=1,
                             color=pdf_colour('silver')))
    story.append(Spacer(1, 0.1 * inch))
