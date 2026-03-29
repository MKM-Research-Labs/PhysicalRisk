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

"""EOD Report - Page 2: Outstanding Positions."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


class EODPositionsPage:
    """Generates the outstanding positions table page."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.section_style = ParagraphStyle(
            'EODSection', parent=styles['Heading2'],
            fontSize=13, spaceBefore=16, spaceAfter=8,
            textColor=colors.HexColor('#1565C0'),
        )

    def get_content(self, snapshot: dict) -> list:
        """Generate positions table elements, grouped by gauge_id."""
        elements = []
        positions = snapshot.get('positions', [])

        elements.append(Paragraph("Outstanding Positions", self.section_style))

        if not positions:
            elements.append(Paragraph("No open positions.",
                                       getSampleStyleSheet()['Normal']))
            return elements

        def fmt_gbp(v):
            if v is None or v == 0:
                return "\u2014"
            sign = "-" if v < 0 else ""
            return f"{sign}\u00a3{abs(v):,.0f}"

        # Group positions by gauge_id
        from collections import defaultdict
        gauge_groups = defaultdict(list)
        for p in positions:
            gauge_groups[p.get('gauge_id', 'Unknown')].append(p)

        # Sort groups by total |daily P&L| descending
        sorted_gauges = sorted(
            gauge_groups.items(),
            key=lambda kv: sum(abs(p.get('daily_pnl', 0)) for p in kv[1]),
            reverse=True)

        col_widths = [
            0.85 * inch, 0.8 * inch, 0.55 * inch, 0.7 * inch,
            0.35 * inch, 0.5 * inch, 0.5 * inch,
            0.65 * inch, 0.7 * inch, 0.7 * inch,
        ]
        num_cols = len(col_widths)

        header = [
            "Swap ID", "Gauge", "Trigger", "Notional",
            "Tenor", "Trade Spd", "Fair Spd",
            "FS01", "Daily P&L", "Running"
        ]
        rows = [header]
        gauge_subheader_rows = []  # Track row indices for styling

        for gauge_id, group in sorted_gauges:
            # Sort trades within group by |daily P&L|
            group.sort(key=lambda p: abs(p.get('daily_pnl', 0)), reverse=True)

            # Gauge subtotals
            g_notional = sum(p.get('notional', 0) for p in group)
            g_fs01 = sum(p.get('gauge_fs01', 0) for p in group)
            g_daily = sum(p.get('daily_pnl', 0) for p in group)
            g_running = sum(p.get('running_pnl', 0) for p in group)

            # Subheader row
            gauge_short = gauge_id if len(gauge_id) <= 16 else gauge_id[:16]
            subheader_text = (
                f"{gauge_short}  ({len(group)} trades)  |  "
                f"Daily: {fmt_gbp(g_daily)}  |  Running: {fmt_gbp(g_running)}")
            subheader_row = [subheader_text] + [''] * (num_cols - 1)
            gauge_subheader_rows.append(len(rows))
            rows.append(subheader_row)

            # Trade rows
            for p in group:
                g_short = p.get('gauge_id', '')
                if len(g_short) > 12:
                    g_short = g_short[:12] + "\u2026"

                rows.append([
                    p.get('swap_id', ''),
                    g_short,
                    (p.get('trigger', '') or '').title(),
                    fmt_gbp(p.get('notional', 0)),
                    f"{p.get('tenor', 0)}Y",
                    f"{p.get('trade_spread_bps', 0):.1f}",
                    f"{p.get('fair_spread_bps', 0):.1f}",
                    fmt_gbp(p.get('gauge_fs01', 0)),
                    fmt_gbp(p.get('daily_pnl', 0)),
                    fmt_gbp(p.get('running_pnl', 0)),
                ])

        # Portfolio total row
        total_notional = sum(p.get('notional', 0) for p in positions)
        total_dv01 = sum(p.get('gauge_fs01', 0) for p in positions)
        total_daily = sum(p.get('daily_pnl', 0) for p in positions)
        total_running = sum(p.get('running_pnl', 0) for p in positions)

        rows.append([
            "TOTAL", "", "", fmt_gbp(total_notional), "",
            "", "", fmt_gbp(total_dv01),
            fmt_gbp(total_daily), fmt_gbp(total_running),
        ])

        t = Table(rows, colWidths=col_widths)

        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]

        # Style gauge subheader rows
        for row_idx in gauge_subheader_rows:
            style_cmds.extend([
                ('SPAN', (0, row_idx), (-1, row_idx)),
                ('BACKGROUND', (0, row_idx), (-1, row_idx),
                 colors.HexColor('#E8EAF6')),
                ('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
                ('FONTSIZE', (0, row_idx), (-1, row_idx), 7),
                ('ALIGN', (0, row_idx), (-1, row_idx), 'LEFT'),
            ])

        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 12))

        return elements
