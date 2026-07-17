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
EOD Report Generator for the Trading Desk.

Orchestrates page modules to create a comprehensive daily P&L report.
Follows the same pattern as GaugeReportGenerator / PropertyReportGenerator.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from .eod_page_01_summary import EODSummaryPage
from .eod_page_02_positions import EODPositionsPage
from .eod_page_03_pnl_detail import EODPnLDetailPage
from .eod_page_04_charts import EODChartsPage

logger = logging.getLogger(__name__)


class EODReportGenerator:
    """Generates EOD PDF reports for the trading desk."""

    def __init__(self, output_dir: Optional[Path] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            from config import config
            self.output_dir = config.get_eod_dir()
        os.makedirs(self.output_dir, exist_ok=True)

        self.pages = {
            'summary': EODSummaryPage(),
            'positions': EODPositionsPage(),
            'pnl_detail': EODPnLDetailPage(),
            'charts': EODChartsPage(),
        }

    def generate_report(self, snapshot: dict,
                        pnl_series: List[dict] = None) -> Path:
        """
        Generate an EOD PDF report.

        Args:
            snapshot: EOD snapshot dictionary
            pnl_series: Historical P&L series for charts

        Returns:
            Path to generated PDF file
        """
        eod_id = snapshot.get('eod_id', 'EOD')
        eod_date = snapshot.get('date', '')
        pdf_path = self.output_dir / f"{eod_id}.pdf"

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.7 * inch,
        )

        story = []

        # Page 1: Summary
        story.extend(self.pages['summary'].get_content(snapshot))
        story.append(PageBreak())

        # Page 2: Positions
        story.extend(self.pages['positions'].get_content(snapshot))
        story.append(PageBreak())

        # Page 3: P&L Detail
        story.extend(self.pages['pnl_detail'].get_content(snapshot))
        story.append(PageBreak())

        # Page 4: Charts
        story.extend(self.pages['charts'].get_content(
            snapshot, pnl_series or []))

        # Footer
        story.append(Spacer(1, 24))
        footer_style = ParagraphStyle(
            'EODFooter', parent=getSampleStyleSheet()['Normal'],
            fontSize=8, textColor=colors.grey,
        )
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            "CONFIDENTIAL - For authorized use only | MKM Research Labs",
            footer_style
        ))

        def _header_footer(canvas, doc):
            canvas.saveState()
            # Header line
            canvas.setStrokeColor(colors.HexColor('#1565C0'))
            canvas.setLineWidth(1)
            canvas.line(0.6 * inch, 10.3 * inch,
                        7.9 * inch, 10.3 * inch)
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(colors.grey)
            canvas.drawString(0.6 * inch, 10.35 * inch,
                              f"EOD Report — {eod_date}")
            canvas.drawRightString(7.9 * inch, 10.35 * inch,
                                    "MKM Research Labs")

            # Footer
            canvas.setFont('Helvetica', 7)
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(4.25 * inch, 0.4 * inch,
                                      f"Page {page_num}")
            canvas.restoreState()

        doc.build(story, onFirstPage=_header_footer,
                  onLaterPages=_header_footer)

        logger.info("EOD PDF generated: %s", pdf_path)
        return pdf_path
