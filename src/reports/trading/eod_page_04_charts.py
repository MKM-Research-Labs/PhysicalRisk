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

"""EOD Report - Page 4: P&L Progression Charts."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.widgets.markers import makeMarker


class EODChartsPage:
    """Generates P&L progression charts for the EOD report."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.section_style = ParagraphStyle(
            'EODSection', parent=styles['Heading2'],
            fontSize=13, spaceBefore=16, spaceAfter=8,
            textColor=colors.HexColor('#1565C0'),
        )

    def get_content(self, snapshot: dict, pnl_series: list) -> list:
        """Generate chart elements."""
        elements = []

        elements.append(Paragraph("P&L Progression", self.section_style))

        if not pnl_series or len(pnl_series) < 2:
            elements.append(Paragraph(
                "Insufficient data for P&L charts. "
                "At least 2 EOD snapshots required.",
                getSampleStyleSheet()['Normal']))
            return elements

        # Chart 1: Running P&L line chart
        elements.append(self._running_pnl_chart(pnl_series))
        elements.append(Spacer(1, 16))

        # Chart 2: Daily P&L bar chart
        elements.append(self._daily_pnl_chart(pnl_series))
        elements.append(Spacer(1, 16))

        # Chart 3: P&L by gauge (from current snapshot positions)
        elements.append(self._pnl_by_gauge_chart(snapshot))

        return elements

    def _running_pnl_chart(self, pnl_series: list) -> Drawing:
        """Create running P&L line chart."""
        width = 480
        height = 180

        d = Drawing(width, height + 30)

        # Title
        d.add(String(10, height + 15, 'Running P&L Over Time',
                      fontSize=10, fillColor=colors.HexColor('#333')))

        # Data
        data = [(p.get('running_pnl', 0)) for p in pnl_series[-30:]]
        n = len(data)

        if n == 0:
            return d

        lp = LinePlot()
        lp.x = 50
        lp.y = 30
        lp.width = width - 80
        lp.height = height - 40
        lp.data = [[(i, v) for i, v in enumerate(data)]]
        lp.lines[0].strokeColor = colors.HexColor('#1565C0')
        lp.lines[0].strokeWidth = 2
        lp.xValueAxis.valueMin = 0
        lp.xValueAxis.valueMax = max(n - 1, 1)
        lp.xValueAxis.labels.fontSize = 7

        # Set labels to dates
        dates = [p.get('date', '')[-5:] for p in pnl_series[-30:]]
        step = max(1, n // 6)
        lp.xValueAxis.labelTextFormat = lambda v: dates[int(v)] if 0 <= int(v) < len(dates) and int(v) % step == 0 else ''

        lp.yValueAxis.labels.fontSize = 7
        lp.yValueAxis.labelTextFormat = lambda v: f'\u00a3{v:,.0f}'

        d.add(lp)
        return d

    def _daily_pnl_chart(self, pnl_series: list) -> Drawing:
        """Create daily P&L bar chart."""
        width = 480
        height = 160

        d = Drawing(width, height + 30)
        d.add(String(10, height + 15, 'Daily P&L',
                      fontSize=10, fillColor=colors.HexColor('#333')))

        series = pnl_series[-30:]
        n = len(series)
        if n == 0:
            return d

        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 30
        bc.width = width - 80
        bc.height = height - 40
        bc.data = [[p.get('daily_pnl', 0) for p in series]]

        # Color bars green/red
        for i, p in enumerate(series):
            if p.get('daily_pnl', 0) >= 0:
                bc.bars[(0, i)].fillColor = colors.HexColor('#4CAF50')
            else:
                bc.bars[(0, i)].fillColor = colors.HexColor('#EF5350')

        bc.categoryAxis.labels.fontSize = 7
        bc.categoryAxis.categoryNames = [
            p.get('date', '')[-5:] for p in series
        ]
        bc.valueAxis.labels.fontSize = 7
        bc.valueAxis.labelTextFormat = lambda v: f'\u00a3{v:,.0f}'
        bc.barWidth = max(2, (width - 100) // n - 2)

        d.add(bc)
        return d

    def _pnl_by_gauge_chart(self, snapshot: dict) -> Drawing:
        """Create horizontal P&L by gauge summary."""
        width = 480
        positions = snapshot.get('positions', [])

        # Aggregate by gauge
        gauge_pnl = {}
        for p in positions:
            gid = p.get('gauge_id', 'Unknown')
            short_gid = gid[:14] if len(gid) > 14 else gid
            gauge_pnl[short_gid] = gauge_pnl.get(short_gid, 0) + p.get(
                'running_pnl', 0)

        if not gauge_pnl:
            d = Drawing(width, 40)
            d.add(String(10, 20, 'No gauge P&L data available.',
                          fontSize=9, fillColor=colors.grey))
            return d

        # Sort by absolute P&L
        sorted_gauges = sorted(gauge_pnl.items(),
                                key=lambda x: abs(x[1]), reverse=True)[:10]

        height = max(80, len(sorted_gauges) * 18 + 40)
        d = Drawing(width, height + 30)
        d.add(String(10, height + 15, 'Running P&L by Gauge (Top 10)',
                      fontSize=10, fillColor=colors.HexColor('#333')))

        # Simple horizontal bars
        bar_area_x = 120
        bar_area_w = width - 150
        max_val = max(abs(v) for _, v in sorted_gauges) or 1

        for i, (gid, pnl) in enumerate(sorted_gauges):
            y = height - 10 - i * 18
            bar_w = abs(pnl) / max_val * bar_area_w * 0.8
            bar_color = (colors.HexColor('#4CAF50') if pnl >= 0
                         else colors.HexColor('#EF5350'))

            # Gauge label
            d.add(String(5, y - 3, gid,
                          fontSize=7, fillColor=colors.HexColor('#333')))

            # Bar
            if pnl >= 0:
                d.add(Rect(bar_area_x, y - 5, bar_w, 10,
                            fillColor=bar_color, strokeColor=None))
            else:
                d.add(Rect(bar_area_x - bar_w, y - 5, bar_w, 10,
                            fillColor=bar_color, strokeColor=None))

            # Value label
            d.add(String(bar_area_x + bar_w + 5 if pnl >= 0 else bar_area_x - bar_w - 50,
                          y - 3,
                          f'\u00a3{pnl:,.0f}',
                          fontSize=7,
                          fillColor=colors.HexColor('#333')))

        return d
