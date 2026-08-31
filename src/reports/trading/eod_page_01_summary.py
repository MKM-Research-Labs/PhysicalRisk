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

"""EOD Report - Page 1: Title and Executive Summary."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reports.theme_pdf import pdf_colour


class EODSummaryPage:
    """Generates the title and P&L summary page."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'EODTitle', parent=styles['Title'],
            fontSize=20, spaceAfter=6, textColor=pdf_colour('accent-mid'),
        )
        self.subtitle_style = ParagraphStyle(
            'EODSubtitle', parent=styles['Normal'],
            fontSize=10, spaceAfter=20, textColor=colors.grey,
        )
        self.section_style = ParagraphStyle(
            'EODSection', parent=styles['Heading2'],
            fontSize=13, spaceBefore=16, spaceAfter=8,
            textColor=pdf_colour('accent-mid'),
        )

    def get_content(self, snapshot: dict) -> list:
        """Generate title + summary elements."""
        elements = []
        summary = snapshot.get('portfolio_summary', {})
        eod_date = snapshot.get('date', '')

        # Title
        elements.append(Paragraph("End of Day Report", self.title_style))
        elements.append(Paragraph(
            f"{eod_date} | MKM Research Labs Physical Risk Trading Desk",
            self.subtitle_style
        ))

        # Executive Summary
        elements.append(Paragraph("Executive Summary", self.section_style))

        def fmt_gbp(v):
            if v is None or v == 0:
                return "GBP 0"
            sign = "-" if v < 0 else ""
            return f"{sign}GBP {abs(v):,.0f}"

        def pnl_color(v):
            return pdf_colour('green-dark') if v >= 0 else pdf_colour('red-dark')

        summary_data = [
            ["Metric", "Value"],
            ["EOD Date", eod_date],
            ["Open Positions", str(summary.get('num_open_trades', 0))],
            ["Total Notional", fmt_gbp(summary.get('total_notional', 0))],
            ["Daily P&L", fmt_gbp(summary.get('total_daily_pnl', 0))],
            ["  From New Trades", fmt_gbp(summary.get('daily_pnl_from_trades', 0))],
            ["  From Market Moves", fmt_gbp(summary.get('daily_pnl_from_market', 0))],
            ["Running P&L (to date)", fmt_gbp(summary.get('total_running_pnl', 0))],
        ]

        t = Table(summary_data, colWidths=[2.8 * inch, 3.5 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), pdf_colour('accent-mid')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 1), (0, -1), pdf_colour('accent-soft')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 16))

        return elements
