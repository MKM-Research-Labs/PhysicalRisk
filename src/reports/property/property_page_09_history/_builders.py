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

"""Historical-risk assessment and gauge-derived flood-history builders."""

import json
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table


class _HistoryBuildersMixin:
    """Historical risk assessment + flood-history table builders."""

    def _assess_historical_risks(self, history_data: Dict[str, Any]) -> Dict[str, str]:
        """Assess risks based on historical data."""
        risk_summary = {}

        # Environmental risk assessment
        environmental = history_data.get('EnvironmentalIssues', {})
        if environmental:
            air_quality = environmental.get('AirQuality', '').lower()
            if 'poor' in air_quality or 'very high' in air_quality:
                risk_summary["Environmental Risk"] = "High - Poor air quality concerns"
            elif 'moderate' in air_quality:
                risk_summary["Environmental Risk"] = "Medium - Moderate environmental concerns"
            else:
                risk_summary["Environmental Risk"] = "Low - Good environmental conditions"

        # Flood risk from history
        flood_events = history_data.get('FloodEvents', {})
        if flood_events:
            damage_severity = flood_events.get('FloodDamageSeverity', '').lower()
            if 'severe' in damage_severity or 'major' in damage_severity:
                risk_summary["Historical Flood Risk"] = "High - Previous severe flood damage"
            elif 'moderate' in damage_severity:
                risk_summary["Historical Flood Risk"] = "Medium - Previous moderate damage"
            elif 'no damage' in damage_severity or 'none' in damage_severity:
                risk_summary["Historical Flood Risk"] = "Low - No previous flood damage"

        # Ground stability risk
        ground_conditions = history_data.get('GroundConditions', {})
        if ground_conditions:
            subsidence = ground_conditions.get('SubsidenceStatus', '').lower()
            if 'major' in subsidence or 'active' in subsidence:
                risk_summary["Ground Stability Risk"] = "High - Active ground movement"
            elif 'minor' in subsidence:
                risk_summary["Ground Stability Risk"] = "Medium - Minor ground movement"
            else:
                risk_summary["Ground Stability Risk"] = "Low - Stable ground conditions"

        return risk_summary

    def _build_flood_history(self, property_data: Dict[str, Any]) -> List:
        """Build flood history from nearest gauge historical daily data."""
        from config import config

        elements = []
        elements.append(Paragraph("Flood History", self.styles['SubSectionHeader']))

        # Find nearest gauge ID
        ph = property_data.get('PropertyHeader', {})
        ref_gauges = ph.get('ReferenceGauges', [])
        if not ref_gauges:
            elements.append(Paragraph("No reference gauges available.", self.styles['Normal']))
            return elements

        gauge_id = ref_gauges[0]

        # Get property elevation
        loc = ph.get('Location', {})
        risk = loc.get('RiskAssessment', ph.get('RiskAssessment', {}))
        prop_elev = risk.get('GroundLevelMeters', 0)
        floor_level = ph.get('Construction', {}).get('FloorLevelMeters', 0)
        flood_threshold = prop_elev + floor_level

        # Load gauge historical daily data
        gaugehd_dir = config.get_gaugehd_dir()
        hd_file = gaugehd_dir / f'gauge_{gauge_id}_hd.json'
        if not hd_file.exists():
            elements.append(Paragraph(
                f"No historical daily data for gauge {gauge_id}.",
                self.styles['Normal']
            ))
            return elements

        try:
            with open(hd_file) as f:
                hd = json.load(f)
        except Exception:
            elements.append(Paragraph("Error loading gauge historical data.", self.styles['Normal']))
            return elements

        stages = hd.get('gauge_metadata', {}).get('flood_stages', {})
        gauge_elev = hd.get('gauge_metadata', {}).get('elevation', 0)
        warning_level = stages.get('FloodWarning', float('inf'))

        # Scan for days where gauge level + gauge elevation could impact property
        obs = hd.get('daily_observations', [])
        flood_days = []
        for o in obs:
            level = o.get('level_meters', 0)
            if level >= warning_level:
                # Water surface elevation at gauge
                wse = gauge_elev + level
                # Estimated depth at property (can be negative = below floor)
                est_depth = wse - flood_threshold
                flood_days.append({
                    'date': o.get('date', ''),
                    'gauge_level': level,
                    'wse': wse,
                    'est_depth': est_depth,
                })

        if not flood_days:
            elements.append(Paragraph(
                f"No flood events recorded at nearest gauge ({gauge_id}) over "
                f"{hd.get('years_included', 50)} years.",
                self.styles['Normal']
            ))
            return elements

        # Group consecutive days into events
        events = []
        current = None
        for day in sorted(flood_days, key=lambda d: d['date']):
            try:
                dt = datetime.strptime(day['date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                continue
            if current is None:
                current = {'start': dt, 'end': dt, 'peak_level': day['gauge_level'],
                           'peak_wse': day['wse'], 'peak_depth': day['est_depth']}
            elif (dt - current['end']).days <= 3:
                current['end'] = dt
                if day['gauge_level'] > current['peak_level']:
                    current['peak_level'] = day['gauge_level']
                    current['peak_wse'] = day['wse']
                    current['peak_depth'] = day['est_depth']
            else:
                events.append(current)
                current = {'start': dt, 'end': dt, 'peak_level': day['gauge_level'],
                           'peak_wse': day['wse'], 'peak_depth': day['est_depth']}
        if current:
            events.append(current)

        events.sort(key=lambda e: e['start'], reverse=True)

        # Property flooded = est_depth > 0
        flooded_count = sum(1 for e in events if e['peak_depth'] > 0)

        header = ['Date', 'Gauge Peak (m)', 'Est. Depth at Property', 'Impact']
        rows = [header]
        for ev in events:
            duration = (ev['end'] - ev['start']).days + 1
            if ev['start'] == ev['end']:
                date_str = ev['start'].strftime('%d %b %Y')
            else:
                date_str = f"{ev['start'].strftime('%d %b %Y')} - {ev['end'].strftime('%d %b %Y')}"
            depth_str = f"{ev['peak_depth']:.2f} m"
            impact = "FLOODED" if ev['peak_depth'] > 0 else "Below floor"
            rows.append([date_str, f"{ev['peak_level']:.2f}", depth_str, impact])

        col_widths = [2.2 * inch, 1.5 * inch, 1.8 * inch, 1.0 * inch]
        table = Table(rows, colWidths=col_widths)
        table.setStyle(self.table_styles.get('flood_risk', self.table_styles['history']))
        elements.append(table)
        elements.append(Spacer(1, self.spacing['table_bottom']))

        years = hd.get('years_included', 50)
        elements.append(Paragraph(
            f"Gauge flood events: {len(events)} over {years} years | "
            f"Estimated property floods: {flooded_count} | "
            f"Nearest gauge: {gauge_id} | "
            f"Property floor: {flood_threshold:.2f} m AOD",
            self.styles['Normal']
        ))

        return elements
