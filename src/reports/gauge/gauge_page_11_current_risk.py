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
Page 11: Current Risk Status
Percentile gauge showing where the current reading sits in the
50-year historical distribution for the same month.
"""

import io
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, Spacer, Table

from .gauge_page_00_base import GaugeBasePage


class GaugeCurrentRiskPage(GaugeBasePage):
    """Generates current risk status page with percentile comparison."""

    def generate_elements(self, gauge_data: Dict[str, Any],
                         timeseries_data: Dict[str, Any] = None) -> List:
        elements = []
        elements.append(Paragraph("Current Risk Status", self.styles['SectionHeader']))
        elements.append(Spacer(1, self.spacing['minor_section']))

        hd = (timeseries_data or {}).get('historical_daily')
        if not hd or not hd.get('daily_observations'):
            elements.append(Paragraph(
                "No historical daily data available for risk comparison.",
                self.styles['Normal']
            ))
            return elements

        obs = hd['daily_observations']
        if not obs:
            elements.append(Paragraph("No observations available.", self.styles['Normal']))
            return elements

        # Current reading = latest observation
        latest = obs[-1]
        current_level = latest.get('level_meters', 0)
        current_date = latest.get('date', 'Unknown')
        try:
            current_dt = datetime.strptime(current_date, '%Y-%m-%d')
            current_month = current_dt.month
            current_month_name = current_dt.strftime('%B')
        except ValueError:
            current_month = None
            current_month_name = 'Unknown'

        # Gather same-month readings across all years
        same_month_levels = []
        all_levels = []
        for o in obs:
            level = o.get('level_meters')
            if level is None:
                continue
            all_levels.append(level)
            try:
                d = datetime.strptime(o['date'], '%Y-%m-%d')
                if current_month and d.month == current_month:
                    same_month_levels.append(level)
            except (ValueError, KeyError):
                continue

        if not same_month_levels:
            same_month_levels = all_levels

        # Calculate percentile
        same_month_levels.sort()
        n = len(same_month_levels)
        rank = sum(1 for x in same_month_levels if x <= current_level)
        percentile = (rank / n) * 100 if n > 0 else 50

        # Build percentile gauge chart
        elements.extend(self._build_percentile_gauge(
            current_level, percentile, current_month_name,
            same_month_levels, current_date, hd
        ))

        return elements

    def _build_percentile_gauge(self, current_level: float, percentile: float,
                                month_name: str, same_month_levels: List[float],
                                current_date: str, hd: Dict) -> List:
        """Build a percentile gauge visualisation."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        elements = []

        # Determine risk category
        if percentile >= 95:
            risk_label = "Very High"
            risk_color = '#B71C1C'
        elif percentile >= 80:
            risk_label = "High"
            risk_color = '#E53935'
        elif percentile >= 60:
            risk_label = "Elevated"
            risk_color = '#FFA726'
        elif percentile >= 40:
            risk_label = "Normal"
            risk_color = '#66BB6A'
        else:
            risk_label = "Low"
            risk_color = '#1976D2'

        # Header text
        elements.append(Paragraph(
            f"Current Reading: <b>{current_level:.2f}m</b> on {current_date}",
            self.styles['Normal']
        ))
        elements.append(Paragraph(
            f"Percentile: <b>{percentile:.0f}th</b> of {month_name} readings over 50 years "
            f"({len(same_month_levels)} observations) — <b>{risk_label}</b>",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, self.spacing['minor_section']))

        # Create gauge dial figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8), dpi=150,
                                        gridspec_kw={'width_ratios': [1, 1.2]})

        # Left: Semi-circular gauge dial
        theta = np.linspace(np.pi, 0, 100)
        # Background arc segments (green-yellow-orange-red)
        segments = [
            (0, 40, '#4CAF50'),    # Low-Normal (green)
            (40, 60, '#8BC34A'),   # Normal (light green)
            (60, 80, '#FFC107'),   # Elevated (amber)
            (80, 95, '#FF5722'),   # High (deep orange)
            (95, 100, '#B71C1C'),  # Very High (dark red)
        ]
        for start, end, color in segments:
            s_idx = int(start)
            e_idx = int(end)
            arc_theta = np.linspace(np.pi * (1 - start / 100), np.pi * (1 - end / 100), e_idx - s_idx + 1)
            for t in arc_theta:
                ax1.plot([0, 0.85 * np.cos(t)], [0, 0.85 * np.sin(t)],
                         color=color, linewidth=3, alpha=0.4)

        # Needle
        needle_angle = np.pi * (1 - percentile / 100)
        ax1.plot([0, 0.75 * np.cos(needle_angle)], [0, 0.75 * np.sin(needle_angle)],
                 color=risk_color, linewidth=2.5)
        ax1.plot(0, 0, 'ko', markersize=5)

        # Labels
        ax1.text(0, -0.15, f"{percentile:.0f}th", ha='center', fontsize=14, fontweight='bold',
                 color=risk_color)
        ax1.text(0, -0.30, "percentile", ha='center', fontsize=8, color='#666')
        ax1.text(-0.9, -0.05, '0', fontsize=7, color='#999')
        ax1.text(0.85, -0.05, '100', fontsize=7, color='#999')
        ax1.set_xlim(-1.1, 1.1)
        ax1.set_ylim(-0.4, 1.0)
        ax1.set_aspect('equal')
        ax1.axis('off')
        ax1.set_title(f'{month_name} Distribution', fontsize=9, fontweight='bold')

        # Right: Histogram with current reading marker
        ax2.hist(same_month_levels, bins=30, color='#90CAF9', edgecolor='#1565C0', alpha=0.7)
        ax2.axvline(x=current_level, color=risk_color, linewidth=2, linestyle='-',
                     label=f'Current: {current_level:.2f}m')

        # Add flood thresholds from metadata
        metadata = hd.get('gauge_metadata', {})
        flood_stages = metadata.get('flood_stages', {})
        if flood_stages.get('FloodAlert'):
            ax2.axvline(x=flood_stages['FloodAlert'], color='#FFA726', linewidth=1,
                         linestyle='--', label=f"Alert ({flood_stages['FloodAlert']:.1f}m)")
        if flood_stages.get('FloodWarning'):
            ax2.axvline(x=flood_stages['FloodWarning'], color='#EF5350', linewidth=1,
                         linestyle='--', label=f"Warning ({flood_stages['FloodWarning']:.1f}m)")

        ax2.set_xlabel('Water Level (m)', fontsize=8)
        ax2.set_ylabel('Frequency', fontsize=8)
        ax2.tick_params(labelsize=7)
        ax2.legend(fontsize=6, loc='upper right')
        ax2.set_title(f'{month_name} Readings (50 years)', fontsize=9, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        img = Image(buf, width=6.5 * inch, height=2.6 * inch)
        elements.append(img)

        # Summary statistics table
        elements.append(Spacer(1, self.spacing['minor_section']))
        elements.append(Paragraph("Distribution Statistics", self.styles['SubSectionHeader']))

        import statistics
        stats_data = [
            ['Metric', f'{month_name} (same month)', 'All Months'],
        ]
        all_obs_levels = [o.get('level_meters', 0) for o in hd.get('daily_observations', [])
                          if o.get('level_meters') is not None]

        for label, data_set in [('Mean', 'mean'), ('Median', 'median'),
                                 ('Std Dev', 'stdev'), ('Min', 'min'), ('Max', 'max')]:
            # statistics has mean/median/stdev; min/max are Python built-ins.
            if data_set in ('min', 'max'):
                fn = min if data_set == 'min' else max
                month_val = fn(same_month_levels) if same_month_levels else 0
                all_val = fn(all_obs_levels) if all_obs_levels else 0
            elif data_set == 'stdev':
                month_val = statistics.stdev(same_month_levels) if len(same_month_levels) > 1 else 0
                all_val = statistics.stdev(all_obs_levels) if len(all_obs_levels) > 1 else 0
            else:
                month_val = getattr(statistics, data_set)(same_month_levels) if same_month_levels else 0
                all_val = getattr(statistics, data_set)(all_obs_levels) if all_obs_levels else 0
            stats_data.append([label, f"{month_val:.3f}m", f"{all_val:.3f}m"])

        table = Table(stats_data, colWidths=[1.5 * inch, 3 * inch, 3 * inch])
        table.setStyle(self.table_styles['standard'])
        elements.append(table)

        return elements
