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

"""EOD Report - Page 3: P&L Detail Breakdown."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


class EODPnLDetailPage:
    """Generates the P&L breakdown page: new trades, market moves."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.section_style = ParagraphStyle(
            'EODSection', parent=styles['Heading2'],
            fontSize=13, spaceBefore=16, spaceAfter=8,
            textColor=colors.HexColor('#1565C0'),
        )
        self.subsection_style = ParagraphStyle(
            'EODSubSection', parent=styles['Heading3'],
            fontSize=11, spaceBefore=10, spaceAfter=6,
            textColor=colors.HexColor('#37474F'),
        )

    def get_content(self, snapshot: dict) -> list:
        """Generate P&L detail elements."""
        elements = []
        positions = snapshot.get('positions', [])

        elements.append(Paragraph("P&L Detail Breakdown", self.section_style))

        def fmt_gbp(v):
            if v is None or v == 0:
                return "\u2014"
            sign = "-" if v < 0 else ""
            return f"{sign}\u00a3{abs(v):,.0f}"

        # Section 1: New Trade P&L
        new_trades = [p for p in positions if p.get('new_trade_pnl', 0) != 0]
        elements.append(Paragraph("New Trade P&L", self.subsection_style))

        if new_trades:
            header = ["Swap ID", "Gauge", "Notional", "Trade Spd", "Fair Spd", "P&L"]
            rows = [header]
            for p in new_trades:
                rows.append([
                    p.get('swap_id', ''),
                    p.get('gauge_id', '')[:14],
                    fmt_gbp(p.get('notional', 0)),
                    f"{p.get('trade_spread_bps', 0):.1f}",
                    f"{p.get('fair_spread_bps', 0):.1f}",
                    fmt_gbp(p.get('new_trade_pnl', 0)),
                ])

            t = Table(rows, colWidths=[
                1.1 * inch, 1.0 * inch, 0.9 * inch,
                0.7 * inch, 0.7 * inch, 0.8 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph(
                "No new trades today.",
                getSampleStyleSheet()['Normal']))

        elements.append(Spacer(1, 12))

        # Section 2: Market Move P&L
        market_movers = [p for p in positions if p.get('market_pnl', 0) != 0]
        market_movers.sort(key=lambda p: abs(p.get('market_pnl', 0)),
                           reverse=True)

        elements.append(Paragraph("Market Move P&L", self.subsection_style))

        if market_movers:
            header = ["Swap ID", "Gauge", "Trigger", "Notional", "Market P&L"]
            rows = [header]
            for p in market_movers[:20]:  # Top 20 movers
                rows.append([
                    p.get('swap_id', ''),
                    p.get('gauge_id', '')[:14],
                    (p.get('trigger', '') or '').title(),
                    fmt_gbp(p.get('notional', 0)),
                    fmt_gbp(p.get('market_pnl', 0)),
                ])

            total_market = sum(p.get('market_pnl', 0) for p in market_movers)
            rows.append(["TOTAL", "", "", "", fmt_gbp(total_market)])

            t = Table(rows, colWidths=[
                1.1 * inch, 1.0 * inch, 0.7 * inch,
                0.9 * inch, 0.9 * inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF3E0')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph(
                "No market move P&L today.",
                getSampleStyleSheet()['Normal']))

        elements.append(Spacer(1, 12))
        return elements
