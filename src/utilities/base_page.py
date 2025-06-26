# Copyright (c) 2025 MKM Research Labs. All rights reserved.
# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# src/utilities/base_page.py

"""
Base class for all report pages.
Provides common functionality, styles, and utilities.
"""

import re
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import TableStyle


class BasePage(ABC):
    """Base class for all report page generators."""
    
    def __init__(self):
        """Initialize base page with common styles and configurations."""
        self._setup_styles()
        self._setup_table_styles()
        self._setup_dimensions()
    
    def _setup_styles(self):
        """Set up paragraph styles for the report."""
        self.styles = getSampleStyleSheet()
        
        # Add custom styles only if they don't already exist
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=8,
                textColor=colors.navy,
                fontName='Helvetica-Bold'
            ))
        
        if 'SubTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=colors.darkblue,
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
        """Set up table styles for different content types."""
        self.table_styles = {
            'standard': TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
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
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
            ]),
            
            'risk': TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
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
                ('BOX', (0, 0), (-1, -1), 1, colors.darkred),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.mistyrose, colors.white])
            ]),
            
            'financial': TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
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
                ('BOX', (0, 0), (-1, -1), 1, colors.darkgreen),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.mintcream, colors.white])
            ]),
            
            'energy': TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
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
                ('BOX', (0, 0), (-1, -1), 1, colors.orange),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.papayawhip, colors.white])
            ]),
            
            'protection': TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
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
                ('BOX', (0, 0), (-1, -1), 1, colors.purple),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lavender, colors.white])
            ]),
            
            'history': TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.brown),
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
                ('BOX', (0, 0), (-1, -1), 1, colors.brown),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.wheat, colors.white])
            ])
        }
    
    def _setup_dimensions(self):
        """Set up spacing and table width configurations."""
        # Spacing configurations
        self.spacing = {
            'major_section': 0.15 * inch,
            'minor_section': 0.08 * inch,
            'table_bottom': 0.05 * inch,
            'paragraph': 0.03 * inch
        }
        
        # Table width configurations (optimized for better space usage)
        self.table_widths = {
            'two_col': [3 * inch, 4.5 * inch],
            'three_col': [2.5 * inch, 3 * inch, 2 * inch],
            'four_col': [1.8 * inch, 2 * inch, 1.8 * inch, 1.9 * inch],
            'risk_table': [2.8 * inch, 2.8 * inch, 1.4 * inch, 0.9 * inch]
        }
    
    def _format_field_name(self, field_name: str) -> str:
        """Format field names to be more readable."""
        # Convert camelCase to Title Case with spaces
        formatted = re.sub(r'([a-z])([A-Z])', r'\1 \2', field_name)
        formatted = formatted.title()
        
        # Handle specific abbreviations
        replacements = {
            'Gbp': 'GBP', 'Kwh': 'kWh', 'Epc': 'EPC', 'Co2e': 'CO2e',
            'Sqm': 'sqm', 'Uprn': 'UPRN', 'Usrn': 'USRN', 'Ea': 'EA',
            'Ltv': 'LTV', 'Dti': 'DTI', 'Id': 'ID'
        }
        
        for old, new in replacements.items():
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
    
    def _format_percentage(self, value: Any) -> str:
        """Format percentage values."""
        if isinstance(value, (int, float)):
            return f"{value:.2f}%"
        return self._format_value(value)
    
    @abstractmethod
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate page elements. Must be implemented by subclasses."""
        pass