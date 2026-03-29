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

"""
Base class for report generators.
Provides common PDF building, header/footer, and page management utilities
shared by gauge, property, and risk report generators.
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, SimpleDocTemplate

logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """Abstract base for all report generators."""

    REPORT_TITLE: str = "Report"
    HEADER_COLOR = colors.darkblue
    SUBTITLE_COLOR = colors.blue

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self._get_default_output_dir()
        os.makedirs(self.output_dir, exist_ok=True)
        self._initialize_pages()

    @abstractmethod
    def _get_default_output_dir(self) -> Path:
        """Return the default output directory from config."""

    @abstractmethod
    def _initialize_pages(self):
        """Initialize self.pages dict and self.categories dict."""

    def _build_pdf(self, output_path: Path,
                   pages_to_include: List[str],
                   **page_kwargs) -> Path:
        """Create the PDF document, generate elements, and build.

        Args:
            output_path: Full path for the output PDF.
            pages_to_include: Ordered list of page names to render.
            **page_kwargs: Data arguments forwarded to each page's
                ``generate_elements()`` method.

        Returns:
            The output_path on success.
        """
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=1.2 * inch,
            bottomMargin=1 * inch
        )

        elements = self._generate_elements(pages_to_include, **page_kwargs)
        element_count = len(elements)

        doc.build(elements,
                  onFirstPage=self._create_header_footer,
                  onLaterPages=self._create_header_footer)

        logger.info(f"Report generated: {output_path}")
        logger.info(f"Pages: {len(pages_to_include)} | Elements: {element_count}")

        return output_path

    def _generate_elements(self, pages_to_include: List[str],
                           **page_kwargs) -> List:
        """Generate all report elements by iterating over pages."""
        elements = []

        for i, page_name in enumerate(pages_to_include):
            if page_name not in self.pages:
                logger.warning(f"Skipping unknown page: {page_name}")
                continue

            try:
                if i > 0:
                    elements.append(PageBreak())

                page_elements = self.pages[page_name].generate_elements(
                    **page_kwargs
                )

                logger.debug(
                    f"Page {page_name} generated {len(page_elements)} elements"
                )
                elements.extend(page_elements)
                logger.info(f"Generated {page_name}")

            except Exception as e:
                logger.error(
                    f"Error generating {page_name}: {str(e)}", exc_info=True
                )
                continue

        logger.debug(f"Total elements in _generate_elements: {len(elements)}")
        return elements

    def _create_header_footer(self, canvas, doc):
        """Add headers and footers to pages."""
        canvas.saveState()

        # Header
        canvas.setFont('Helvetica-Bold', 10)
        canvas.setFillColor(self.HEADER_COLOR)
        canvas.drawString(
            0.5 * inch, doc.height + doc.topMargin, "MKM Research Labs"
        )

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(self.SUBTITLE_COLOR)
        canvas.drawRightString(
            doc.width + 0.5 * inch,
            doc.height + doc.topMargin - 0.1 * inch,
            self.REPORT_TITLE
        )
        canvas.drawRightString(
            doc.width + 0.5 * inch,
            doc.height + doc.topMargin - 0.3 * inch,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(
            0.5 * inch,
            doc.bottomMargin - 0.5 * inch,
            f"Page {canvas.getPageNumber()}"
        )
        canvas.drawCentredString(
            doc.width / 2.0 + 0.5 * inch,
            doc.bottomMargin - 0.5 * inch,
            "CONFIDENTIAL - For authorized use only"
        )

        # Footer line
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(
            0.5 * inch, doc.bottomMargin - 0.25 * inch,
            doc.width + 0.5 * inch, doc.bottomMargin - 0.25 * inch
        )

        canvas.restoreState()

    # Utility methods
    def list_available_pages(self) -> List[str]:
        """Return list of available pages."""
        return list(self.pages.keys())

    def get_page_categories(self) -> Dict[str, List[str]]:
        """Return page categories."""
        return self.categories.copy()

    def validate_pages(self, pages: List[str]) -> tuple:
        """Validate page list, return (valid_pages, invalid_pages)."""
        valid = [p for p in pages if p in self.pages]
        invalid = [p for p in pages if p not in self.pages]
        return valid, invalid
