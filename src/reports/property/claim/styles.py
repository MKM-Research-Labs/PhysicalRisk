# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Paragraph styles used across all claim report pages."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


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
         textColor=colors.HexColor('#1A237E'),
         alignment=TA_CENTER,
         spaceAfter=6)

    _add('ClaimSubTitle',
         parent=base['Normal'],
         fontSize=14,
         fontName='Helvetica',
         textColor=colors.HexColor('#283593'),
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
         textColor=colors.HexColor('#1A237E'),
         spaceBefore=10,
         spaceAfter=4)

    _add('SubSectionHeader',
         parent=base['Normal'],
         fontSize=11,
         fontName='Helvetica-Bold',
         textColor=colors.HexColor('#1B5E20'),
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
         textColor=colors.HexColor('#4A148C'))

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
         textColor=colors.HexColor('#546E7A'),
         alignment=TA_CENTER)

    _add('SignatureLine',
         parent=base['Normal'],
         fontSize=9,
         leading=13,
         textColor=colors.HexColor('#212121'))

    _add('StatsBar',
         parent=base['Normal'],
         fontSize=9,
         fontName='Helvetica-Bold',
         textColor=colors.HexColor('#37474F'),
         alignment=TA_CENTER)

    return base
