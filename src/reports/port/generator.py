# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

"""
Portfolio Generation Report — PDF output.

Generates a comprehensive PDF summarising the output of `app.py port`.
Each pipeline step gets its own section with detailed item-level tables:

  1. Gauge Network     — gauge listing with thresholds + tidal info
  2. Properties        — property listing with type / lat / lon
  3. Mortgages         — mortgage listing with LTV / term
  4. Historical Gauges — gaugehd file listing with seasonal baselines
  5. Storm Sequences   — sequence summary (types, precipitation, duration)
  6. Hazard Curves     — per-gauge GEV exceedance points
  7. Property Flood TS — flood event summary
  8. Property Hazard   — PRS pricing summary
  9. Counterparties    — counterparty listing
  10. Trading Book     — blotter summary
  Summary              — aggregate statistics (mirrors terminal output)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from .styles import StylesMixin, BLUE, GREY
from .data_loader import DataLoaderMixin
from .sections import AnalysisSectionsMixin
from .sections_portfolio import PortfolioSectionsMixin

logger = logging.getLogger(__name__)


class PortReportGenerator(StylesMixin, DataLoaderMixin, PortfolioSectionsMixin, AnalysisSectionsMixin):
    """Generates the portfolio generation PDF report."""

    def __init__(self, input_dir: Path, output_path: Optional[Path] = None):
        self.input_dir = Path(input_dir)
        if output_path:
            self.output_path = Path(output_path)
        else:
            from config import config
            audit_dir = config.get_output_dir() / 'audit'
            audit_dir.mkdir(parents=True, exist_ok=True)
            self.output_path = audit_dir / f'port_{self.input_dir.name}.pdf'
        self._styles = getSampleStyleSheet()
        self._setup_styles()

    def generate(self) -> Path:
        """Generate the portfolio report PDF.

        Returns:
            Path to generated PDF file.
        """
        data = self._load_all()
        now = datetime.now()

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            leftMargin=0.6 * inch,
            rightMargin=0.6 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.7 * inch,
        )

        story = []

        # Title page
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph('MKM Portfolio Generation Report', self.title_style))
        story.append(Paragraph(now.strftime('%d %B %Y  %H:%M'), self.subtitle_style))
        story.append(Paragraph(f'Catchment: {self.input_dir.name}', self.subtitle_style))
        story.append(Spacer(1, 0.3 * inch))

        # Section 1: Gauges
        story.extend(self._section_gauges(data))
        story.append(PageBreak())

        # Section 2: Properties
        story.extend(self._section_properties(data))
        story.append(PageBreak())

        # Section 3: Mortgages
        story.extend(self._section_mortgages(data))
        story.append(PageBreak())

        # Section 4: Historical Gauges
        story.extend(self._section_gaugehd(data))
        story.append(PageBreak())

        # Section 5: Storm Sequences + Stress
        story.extend(self._section_storms(data))
        story.append(Spacer(1, 12))

        # Section 6: Hazard Curves
        story.extend(self._section_hazard_curves(data))
        story.append(PageBreak())

        # Section 7/8: Property TS + Hazard
        story.extend(self._section_propertyts(data))
        story.append(Spacer(1, 12))

        # Section 9: Counterparties
        story.extend(self._section_counterparties(data))
        story.append(PageBreak())

        # Section 10: Trading Book
        story.extend(self._section_blotter(data))
        story.append(Spacer(1, 12))

        # Summary
        story.extend(self._section_summary(data))

        # Footer
        story.append(Spacer(1, 24))
        footer_style = ParagraphStyle(
            'PortFooter', parent=self._styles['Normal'],
            fontSize=8, textColor=GREY,
        )
        story.append(Paragraph(
            f'Generated: {now.strftime("%Y-%m-%d %H:%M:%S")} | '
            'CONFIDENTIAL - For authorized use only | MKM Research Labs',
            footer_style,
        ))

        def _header_footer(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(BLUE)
            canvas.setLineWidth(1)
            canvas.line(0.6 * inch, 10.3 * inch, 7.9 * inch, 10.3 * inch)
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(GREY)
            canvas.drawString(0.6 * inch, 10.35 * inch,
                              'Portfolio Generation Report')
            canvas.drawRightString(7.9 * inch, 10.35 * inch,
                                    'MKM Research Labs')
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(4.25 * inch, 0.4 * inch,
                                      f'Page {page_num}')
            canvas.line(0.6 * inch, 0.55 * inch, 7.9 * inch, 0.55 * inch)
            canvas.restoreState()

        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)

        logger.info('Port report PDF generated: %s', self.output_path)
        return self.output_path
