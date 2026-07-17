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
Mortgage Report Generator.
Generates standalone mortgage analysis reports with property context.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, SimpleDocTemplate

from reports.property.property_page_11_rloan_overview import RLoanOverviewPage
from reports.property.property_page_11a_rloan_details import RLoanDetailsPage
from reports.property.property_page_11b_rloan_costs import RLoanCostsPage
from reports.property.property_page_12_current_status import CurrentStatusPage
from reports.property.property_page_14_borrower_profile import BorrowerProfilePage

from .rloan_page_01_title import RLoanTitlePage

logger = logging.getLogger(__name__)


class RLoanReportGenerator:
    """Generates standalone residential-loan analysis PDF reports."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            from config import config
            self.output_dir = config.get_property_reports_dir()
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()

    def _initialize_pages(self):
        self.pages = {
            'title': RLoanTitlePage(),
            'mortgage_overview': RLoanOverviewPage(),
            'mortgage_details': RLoanDetailsPage(),
            'mortgage_costs': RLoanCostsPage(),
            'current_status': CurrentStatusPage(),
            'borrower_profile': BorrowerProfilePage(),
        }
        self.page_order = [
            'title', 'mortgage_overview', 'mortgage_details',
            'mortgage_costs', 'current_status', 'borrower_profile',
        ]

    def generate_report(self, property_data: Dict[str, Any],
                        rloan_data: Dict[str, Any],
                        output_filename: Optional[str] = None) -> Path:
        if output_filename is None:
            output_filename = self._generate_filename(rloan_data)

        output_path = self.output_dir / output_filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=1.2 * inch,
            bottomMargin=1 * inch,
        )

        elements = self._generate_elements(property_data, rloan_data)
        element_count = len(elements)

        doc.build(
            elements,
            onFirstPage=self._create_header_footer,
            onLaterPages=self._create_header_footer,
        )

        logger.info(f"Mortgage report generated: {output_path}")
        logger.info(f"Pages: {len(self.page_order)} | Elements: {element_count}")
        return output_path

    def _generate_elements(self, property_data, rloan_data):
        elements = []
        for i, page_name in enumerate(self.page_order):
            if page_name not in self.pages:
                continue
            try:
                if i > 0:
                    elements.append(PageBreak())
                page_elements = self.pages[page_name].generate_elements(
                    property_data, rloan_data
                )
                elements.extend(page_elements)
            except Exception as e:
                logger.error(f"Error generating mortgage page {page_name}: {e}")
                continue
        return elements

    def _generate_filename(self, rloan_data):
        try:
            mort = rloan_data.get('RLoan', rloan_data)
            mortgage_id = mort.get('Header', {}).get('RLoanID', 'unknown')
        except (KeyError, TypeError, AttributeError):
            mortgage_id = 'unknown'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"mortgage_report_{mortgage_id}_{timestamp}.pdf"

    def _create_header_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(colors.navy)
        canvas.drawString(0.5 * inch, doc.height + doc.topMargin, "MKM Research Labs")

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.darkblue)
        canvas.drawRightString(
            doc.width + 0.5 * inch,
            doc.height + doc.topMargin - 0.1 * inch,
            "Mortgage Analysis Report",
        )
        canvas.drawRightString(
            doc.width + 0.5 * inch,
            doc.height + doc.topMargin - 0.3 * inch,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )

        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(0.5 * inch, doc.bottomMargin - 0.5 * inch,
                          f"Page {canvas.getPageNumber()}")
        canvas.drawCentredString(
            doc.width / 2.0 + 0.5 * inch,
            doc.bottomMargin - 0.5 * inch,
            "CONFIDENTIAL - For authorized use only",
        )

        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(0.5 * inch, doc.bottomMargin - 0.25 * inch,
                    doc.width + 0.5 * inch, doc.bottomMargin - 0.25 * inch)

        canvas.restoreState()


def generate_rloan_report(property_data: Dict[str, Any],
                          rloan_data: Dict[str, Any],
                          output_dir: Optional[Union[str, Path]] = None,
                          auto_open: bool = False) -> Path:
    """Convenience function to generate a residential-loan report."""
    generator = RLoanReportGenerator(output_dir)
    return generator.generate_report(property_data, rloan_data)
