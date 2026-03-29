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
Page 8: Flood History
50-year historical water level graph with warning thresholds,
plus top worst storm scenarios table.
"""

import io
from typing import Any, Dict, List

from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, Spacer, Table

from .gauge_page_00_base import GaugeBasePage


class GaugeFloodHistoryPage(GaugeBasePage):
    """Generates flood history page with historical graph and worst storms."""

    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        elements = []
        elements.append(Paragraph("Flood History", self.styles['SectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        # --- Section 1: Historical Water Level Graph ---
        hd = (timeseries_data or {}).get('historical_daily')
        if hd and hd.get('daily_observations'):
            elements.extend(self._build_historical_graph(hd))
        else:
            elements.append(Paragraph(
                "No historical daily data available for this gauge.",
                self.styles['Normal']
            ))

        # --- Section 1b: Realised Flood Events ---
        if hd and hd.get('daily_observations'):
            elements.append(Spacer(1, self.spacing['major_section']))
            elements.extend(self._build_realised_floods(hd))

        elements.append(Spacer(1, self.spacing['major_section']))

        # --- Section 2: Top Worst Storm Scenarios ---
        storm_responses = []
        if timeseries_data:
            storm_responses = timeseries_data.get('storm_responses', [])

        if storm_responses:
            elements.extend(self._build_worst_storms_table(storm_responses))
        else:
            elements.append(Paragraph(
                "No storm response data available.",
                self.styles['Normal']
            ))

        return elements

    def _build_historical_graph(self, hd: Dict[str, Any]) -> List:
        """Build a matplotlib chart of 50-year daily water levels with warning thresholds."""
        import matplotlib
        matplotlib.use('Agg')
        from datetime import datetime

        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt

        elements = []
        elements.append(Paragraph("Historical Water Levels (50 Years)", self.styles['SubSectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        obs = hd['daily_observations']
        dates = []
        levels = []
        for o in obs:
            try:
                d = datetime.strptime(o['date'], '%Y-%m-%d')
                dates.append(d)
                levels.append(o['level_meters'])
            except (ValueError, KeyError):
                continue

        if not dates:
            elements.append(Paragraph("Could not parse historical observations.", self.styles['Normal']))
            return elements

        # Extract flood thresholds
        metadata = hd.get('gauge_metadata', {})
        flood_stages = metadata.get('flood_stages', {})
        alert_level = flood_stages.get('FloodAlert')
        warning_level = flood_stages.get('FloodWarning')
        severe_level = flood_stages.get('SevereFloodWarning')

        # Create plot
        fig, ax = plt.subplots(figsize=(7.0, 3.0), dpi=150)
        ax.plot(dates, levels, color='#1976D2', linewidth=0.3, alpha=0.7)

        # Warning level lines
        if alert_level:
            ax.axhline(y=alert_level, color='#FFA726', linestyle='--', linewidth=1.0, label=f'Alert ({alert_level:.1f}m)')
        if warning_level:
            ax.axhline(y=warning_level, color='#EF5350', linestyle='--', linewidth=1.0, label=f'Warning ({warning_level:.1f}m)')
        if severe_level:
            ax.axhline(y=severe_level, color='#B71C1C', linestyle='-', linewidth=1.2, label=f'Severe ({severe_level:.1f}m)')

        ax.set_xlabel('Date', fontsize=8)
        ax.set_ylabel('Water Level (m)', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.xaxis.set_major_locator(mdates.YearLocator(10))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        # Convert to ReportLab Image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        img = Image(buf, width=6.5 * inch, height=2.8 * inch)
        elements.append(img)

        # Summary stats
        stats = hd.get('statistics', {})
        exceedances = stats.get('flood_exceedances', {})
        summary_text = []
        if stats.get('total_years'):
            summary_text.append(f"Record span: {stats['total_years']:.0f} years")
        if stats.get('max_level'):
            summary_text.append(f"Maximum recorded: {stats['max_level']:.2f}m")
        for key, label in [('flood_alert', 'Alert'), ('flood_warning', 'Warning'), ('severe_warning', 'Severe')]:
            exc = exceedances.get(key, {})
            if exc.get('count') is not None:
                summary_text.append(f"{label} exceedances: {exc['count']} ({exc.get('frequency_per_year', 0):.2f}/yr)")

        if summary_text:
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph(
                " | ".join(summary_text),
                self.styles['Normal']
            ))

        return elements

    def _build_realised_floods(self, hd: Dict[str, Any]) -> List:
        """Build a table of realised historic flood events from daily observations."""
        from datetime import datetime
        elements = []
        elements.append(Paragraph("Realised Flood Events", self.styles['SubSectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        stages = hd.get('gauge_metadata', {}).get('flood_stages', {})
        alert_level = stages.get('FloodAlert', float('inf'))
        warning_level = stages.get('FloodWarning', float('inf'))
        severe_level = stages.get('SevereFloodWarning', float('inf'))

        # Scan for days exceeding alert level
        obs = hd.get('daily_observations', [])
        exceedance_days = []
        for o in obs:
            level = o.get('level_meters', 0)
            if level >= alert_level:
                exceedance_days.append({
                    'date': o.get('date', ''),
                    'level': level,
                })

        if not exceedance_days:
            elements.append(Paragraph("No flood events recorded in the historical period.", self.styles['Normal']))
            return elements

        # Group consecutive days (within 3 days) into flood events
        events = []
        current_event = None
        for day in sorted(exceedance_days, key=lambda d: d['date']):
            try:
                dt = datetime.strptime(day['date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                continue

            if current_event is None:
                current_event = {
                    'start': dt, 'end': dt,
                    'peak': day['level'], 'peak_date': dt,
                }
            elif (dt - current_event['end']).days <= 3:
                current_event['end'] = dt
                if day['level'] > current_event['peak']:
                    current_event['peak'] = day['level']
                    current_event['peak_date'] = dt
            else:
                events.append(current_event)
                current_event = {
                    'start': dt, 'end': dt,
                    'peak': day['level'], 'peak_date': dt,
                }
        if current_event:
            events.append(current_event)

        # Sort by date descending
        events.sort(key=lambda e: e['start'], reverse=True)

        # Classify severity
        def classify(peak):
            if peak >= severe_level:
                return 'Severe'
            elif peak >= warning_level:
                return 'Warning'
            return 'Alert'

        header = ['Date Range', 'Peak Level (m)', 'Duration', 'Severity']
        rows = [header]
        for ev in events:
            duration = (ev['end'] - ev['start']).days + 1
            if ev['start'] == ev['end']:
                date_str = ev['start'].strftime('%d %b %Y')
            else:
                date_str = f"{ev['start'].strftime('%d %b %Y')} - {ev['end'].strftime('%d %b %Y')}"
            rows.append([
                date_str,
                f"{ev['peak']:.2f}",
                f"{duration} day{'s' if duration > 1 else ''}",
                classify(ev['peak']),
            ])

        col_widths = [2.5 * inch, 1.5 * inch, 1.2 * inch, 1.3 * inch]
        table = Table(rows, colWidths=col_widths)
        table.setStyle(self.table_styles['flood_risk'])
        elements.append(table)
        elements.append(Spacer(1, self.spacing['table_bottom']))
        elements.append(Paragraph(
            f"Total flood events: {len(events)} over {hd.get('years_included', 50)} years",
            self.styles['Normal']
        ))

        return elements

    def _build_worst_storms_table(self, storm_responses: List[Dict]) -> List:
        """Build table of top 10 worst storm scenarios by peak water level."""
        elements = []
        elements.append(Paragraph("Top 10 Worst Storm Scenarios", self.styles['SubSectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        # Sort by peak water level descending
        sorted_storms = sorted(
            storm_responses,
            key=lambda sr: sr.get('peak_level_m', sr.get('peak_water_level_m', 0)),
            reverse=True
        )[:10]

        header = ['Rank', 'Storm ID', 'Peak Level (m)', 'Level Change (m)', 'Status']
        rows = [header]
        for i, sr in enumerate(sorted_storms, 1):
            storm_id = str(sr.get('storm_id', 'N/A'))[:16]
            peak = sr.get('peak_level_m', sr.get('peak_water_level_m'))
            peak_str = f"{peak:.2f}" if isinstance(peak, (int, float)) else 'N/A'
            change = sr.get('level_change_m')
            change_str = f"{change:.2f}" if isinstance(change, (int, float)) else 'N/A'
            if sr.get('exceeded_severe'):
                status = 'Severe'
            elif sr.get('exceeded_warning'):
                status = 'Warning'
            elif sr.get('exceeded_alert'):
                status = 'Alert'
            else:
                status = 'Normal'
            rows.append([str(i), storm_id, peak_str, change_str, status])

        col_widths = [0.5 * inch, 2.0 * inch, 1.5 * inch, 1.5 * inch, 1.0 * inch]
        table = Table(rows, colWidths=col_widths)
        table.setStyle(self.table_styles['flood_risk'])
        elements.append(table)
        elements.append(Spacer(1, self.spacing['table_bottom']))

        # Overall summary
        total = len(storm_responses)
        alert_count = sum(1 for sr in storm_responses if sr.get('exceeded_alert'))
        warning_count = sum(1 for sr in storm_responses if sr.get('exceeded_warning'))
        severe_count = sum(1 for sr in storm_responses if sr.get('exceeded_severe'))
        elements.append(Paragraph(
            f"Total storms: {total} | Alert: {alert_count} | Warning: {warning_count} | Severe: {severe_count}",
            self.styles['Normal']
        ))

        return elements
