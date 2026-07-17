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

"""
Shared base class for all PDF report pages.
Provides common styles, table styles, dimensions, and formatting utilities
used by gauge, property, and risk report page generators.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle


class ReportBasePage(ABC):
    """Abstract base class for all report page generators."""

    ABBREVIATIONS: Dict[str, str] = {
        'Id': 'ID', 'Api': 'API', 'Uk': 'UK', 'Sqm': 'sqm'
    }

    def __init__(self):
        """Initialize base page with common styles and configurations."""
        self._setup_styles()
        self._setup_table_styles()
        self._setup_dimensions()

    def _setup_styles(self):
        """Set up paragraph styles common to all reports."""
        self.styles = getSampleStyleSheet()

        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=8,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold'
            ))

        if 'SubTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.blue,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            ))

        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading3'],
                fontSize=13,
                textColor=colors.darkblue,
                spaceAfter=4,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            ))

        if 'SubSectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubSectionHeader',
                parent=self.styles['Heading4'],
                fontSize=11,
                textColor=colors.darkgreen,
                spaceAfter=3,
                spaceBefore=8,
                fontName='Helvetica-Bold'
            ))

    def _setup_table_styles(self):
        """Set up the standard table style. Subclasses add domain-specific styles."""
        self.table_styles = {
            'standard': self._make_table_style(
                colors.darkblue, colors.black, colors.lightblue
            )
        }

    @staticmethod
    def _make_table_style(header_color, box_color, row_alt_color):
        """Create a TableStyle with the given colour scheme.

        All report table styles follow the same structure, differing only in
        header background, box border colour, and alternating row colour.
        """
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, box_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_alt_color, colors.white])
        ])

    def _setup_dimensions(self):
        """Set up spacing and table width configurations."""
        self.spacing = {
            'major_section': 0.15 * inch,
            'minor_section': 0.08 * inch,
            'table_bottom': 0.05 * inch,
            'paragraph': 0.03 * inch
        }

        self.table_widths = {
            'two_col': [3 * inch, 4.5 * inch],
            'three_col': [2.5 * inch, 3 * inch, 2 * inch],
            'four_col': [1.8 * inch, 2 * inch, 1.8 * inch, 1.9 * inch],
        }

    def _format_field_name(self, field_name: str) -> str:
        """Format camelCase field names to readable Title Case."""
        formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', field_name)
        formatted = formatted.title()

        for old, new in self.ABBREVIATIONS.items():
            formatted = formatted.replace(old, new)

        return formatted

    def _format_value(self, value: Any) -> str:
        """Format values for display in tables."""
        if value is None:
            return 'Not specified'
        elif isinstance(value, bool):
            return 'Yes' if value else 'No'
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            elif isinstance(value, float):
                return f"{value:.2f}"
            else:
                return str(value)
        elif isinstance(value, str) and value.strip() == '':
            return 'Not specified'
        else:
            return str(value)

    def _format_currency(self, value: Any, currency: str = '£') -> str:
        """Format currency values."""
        if isinstance(value, (int, float)):
            return f"{currency}{value:,.2f}"
        return self._format_value(value)

    def _format_percentage(self, value: Any, decimals: int = 2) -> str:
        """Format percentage values."""
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}%"
        return self._format_value(value)

    def _format_count(self, value: Any) -> str:
        """Format count values with thousands separator."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return self._format_value(value)

    @abstractmethod
    def generate_elements(self, data: Dict[str, Any], **kwargs) -> List:
        """Generate page elements. Must be implemented by subclasses."""
        pass
