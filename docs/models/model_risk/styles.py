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

"""Shared colours, styles, and table helpers for the model risk report."""

import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import (
        HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
        Table, TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

NAVY = colors.HexColor('#1A237E')
STEEL = colors.HexColor('#37474F')
BLUE = colors.HexColor('#1565C0')
GREEN = colors.HexColor('#2E7D32')
AMBER = colors.HexColor('#E65100')
RED = colors.HexColor('#B71C1C')
LIGHT_GREEN = colors.HexColor('#E8F5E9')
LIGHT_AMBER = colors.HexColor('#FFF3E0')
LIGHT_RED = colors.HexColor('#FFEBEE')
LIGHT_BG = colors.HexColor('#F5F5F5')

RAG_COLOURS = {
    'Green': GREEN, 'Amber': AMBER, 'Red': RED,
    'green': GREEN, 'amber': AMBER, 'red': RED,
}
RAG_BG = {
    'Green': LIGHT_GREEN, 'Amber': LIGHT_AMBER, 'Red': LIGHT_RED,
    'green': LIGHT_GREEN, 'amber': LIGHT_AMBER, 'red': LIGHT_RED,
}


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------

def get_styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'MRTitle', parent=base['Heading1'],
            fontSize=24, textColor=NAVY, spaceAfter=8,
            alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'subtitle': ParagraphStyle(
            'MRSub', parent=base['Normal'],
            fontSize=12, textColor=STEEL, spaceAfter=4,
            alignment=TA_CENTER),
        'meta': ParagraphStyle(
            'MRMeta', parent=base['Normal'],
            fontSize=9, textColor=colors.HexColor('#546E7A'),
            alignment=TA_CENTER, spaceAfter=2),
        'h2': ParagraphStyle(
            'MRH2', parent=base['Heading2'],
            fontSize=13, textColor=NAVY,
            spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'),
        'h3': ParagraphStyle(
            'MRH3', parent=base['Heading3'],
            fontSize=10, textColor=STEEL,
            spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'),
        'body': ParagraphStyle(
            'MRBody', parent=base['BodyText'],
            fontSize=9, leading=13),
        'small': ParagraphStyle(
            'MRSmall', parent=base['Normal'],
            fontSize=7.5, textColor=colors.HexColor('#78909C'), leading=11),
        'note': ParagraphStyle(
            'MRNote', parent=base['BodyText'],
            fontSize=8, leading=11,
            textColor=colors.HexColor('#666666'), leftIndent=12),
    }


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def tbl_style():
    return TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',      (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, 0), 8),
        ('ALIGN',          (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING',  (0, 0), (-1, 0), 7),
        ('BACKGROUND',     (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#f4f6f9')]),
        ('FONTNAME',       (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 1), (-1, -1), 7.5),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('TOPPADDING',     (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING',  (0, 1), (-1, -1), 3),
    ])


def section_rule(story):
    story.append(Spacer(1, 0.12 * inch))
    story.append(HRFlowable(width='100%', thickness=1,
                             color=colors.HexColor('#bdc3c7')))
    story.append(Spacer(1, 0.08 * inch))
