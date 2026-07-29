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
PRS Portfolio Report — property hazard curve waterfall by zone.

Generates a PDF showing every property's spread decomposition,
grouped by EA flood zone, with zone summary statistics.

Usage:
    from reports.port.prs_report import PRSPortfolioReport
    report = PRSPortfolioReport(input_dir)
    path = report.generate()
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)


class PRSPortfolioReport:
    """Generate PRS portfolio report with waterfall tables by zone."""

    def __init__(self, input_dir: Path, output_path: Optional[Path] = None):
        self.input_dir = Path(input_dir)
        if output_path:
            self.output_path = Path(output_path)
        else:
            from config import config
            # PRS portfolio report is a port deliverable, not part of the
            # `phys.py test` audit sequence — keep it under audit/archive/.
            archive_dir = config.get_output_dir() / 'audit' / 'archive'
            archive_dir.mkdir(parents=True, exist_ok=True)
            self.output_path = archive_dir / 'prs_portfolio_report.pdf'
        self._styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.title_style = ParagraphStyle(
            'PRSTitle', parent=self._styles['Title'],
            fontSize=18, spaceAfter=6,
        )
        self.subtitle_style = ParagraphStyle(
            'PRSSubtitle', parent=self._styles['Normal'],
            fontSize=11, textColor=colors.grey, spaceAfter=12,
        )
        self.heading_style = ParagraphStyle(
            'PRSHeading', parent=self._styles['Heading2'],
            fontSize=13, spaceBefore=12, spaceAfter=6,
        )
        self.body_style = self._styles['Normal']

    def generate(self) -> Path:
        """Generate the PRS portfolio report PDF."""
        data = self._load_data()
        now = datetime.now()

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=landscape(letter),
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        story = []

        # Title
        story.append(Paragraph('PRS Portfolio Report', self.title_style))
        story.append(Paragraph(
            f'{now.strftime("%d %B %Y %H:%M")}  |  Catchment: {self.input_dir.name}  |  '
            f'{data["num_properties"]} properties  |  '
            f'{data["num_storms"]:,} storm scenarios',
            self.subtitle_style))
        story.append(Spacer(1, 0.2 * inch))

        # Zone summary
        story.append(Paragraph('Zone Summary', self.heading_style))
        story.append(self._zone_summary_table(data))
        story.append(Spacer(1, 0.2 * inch))

        # Property tables by zone
        for zone in ['Zone 3b', 'Zone 3a', 'Zone 2', 'Zone 1']:
            props = data['by_zone'].get(zone, [])
            if not props:
                continue
            story.append(Paragraph(f'{zone}  ({len(props)} properties)', self.heading_style))
            story.append(self._zone_property_table(props, data['num_storms']))
            story.append(Spacer(1, 0.15 * inch))

        doc.build(story)
        return self.output_path

    def _load_data(self) -> Dict:
        """Load property hazard curves (flood/shd/she) + storm sequences via the seam."""
        import database
        catchment = database.active_catchment()
        hc = database.get_property_hazard_curves(catchment, mode="flood") or {}
        shd_curves = (database.get_property_hazard_curves(catchment, mode="shd")
                      or {}).get('property_hazard_curves', {})
        she_curves = (database.get_property_hazard_curves(catchment, mode="she")
                      or {}).get('property_hazard_curves', {})

        hc_curves = hc.get('property_hazard_curves', {})

        # Get num_storms from propertyhc metadata, fall back to storm_sequences
        num_storms = hc.get('metadata', {}).get('num_storms', 0)
        seq_data = database.get_storm_sequences(catchment)
        if seq_data:
            num_storms = seq_data.get('num_sequences', num_storms)

        # Build per-property records
        by_zone = {}
        for pid, pc in hc_curves.items():
            zone = pc.get('flood_zone', 'Unknown')
            sd = pc.get('spread_decomposition', {})
            ngs = pc.get('nearest_gauges', [])
            synth_ng = next((ng for ng in ngs if ng['gauge_id'].startswith('SYNTH')), None)
            if not synth_ng:
                continue

            shd_pc = shd_curves.get(pid, {})
            she_pc = she_curves.get(pid, {})

            def get_spread(ppc):
                return ppc.get('term_structure', {}).get('severe', {}).get(
                    'prs_spread_bps', [0])[0]

            rec = {
                'pid': pid,
                'zone': zone,
                'dist_m': synth_ng['distance_km'] * 1000,
                'offset': pc['elevation_m'] - synth_ng['gauge_elevation_m'],
                'floor': pc.get('floor_level_m', 0),
                'flood_count': pc.get('flood_count', 0),
                'gauge_spread': sd.get('gauge_spread_bps', 0),
                'shd_spread': get_spread(shd_pc),
                'she_spread': get_spread(she_pc),
                'prop_spread': get_spread(pc),
                'basis': sd.get('gauge_spread_bps', 0) - get_spread(pc),
                'transmission': synth_ng.get('flood_transmission_rate', 0),
            }

            if zone not in by_zone:
                by_zone[zone] = []
            by_zone[zone].append(rec)

        # Sort each zone by spread descending
        for zone in by_zone:
            by_zone[zone].sort(key=lambda r: -r['prop_spread'])

        return {
            'num_properties': len(hc_curves),
            'num_storms': num_storms,
            'by_zone': by_zone,
        }

    def _zone_summary_table(self, data: Dict) -> Table:
        """Build zone summary table."""
        headers = ['Zone', 'Count', 'Avg Floods', 'Avg Spread (bp)',
                   'Min (bp)', 'Max (bp)', 'Avg Gauge (bp)', 'Avg Basis (bp)']
        rows = [headers]

        for zone in ['Zone 3b', 'Zone 3a', 'Zone 2', 'Zone 1']:
            props = data['by_zone'].get(zone, [])
            if not props:
                rows.append([zone, 0, '', '', '', '', '', ''])
                continue
            n = len(props)
            spreads = [p['prop_spread'] for p in props]
            floods = [p['flood_count'] for p in props]
            gauges = [p['gauge_spread'] for p in props]
            bases = [p['basis'] for p in props]
            rows.append([
                zone, n,
                f'{sum(floods)/n:.0f}',
                f'{sum(spreads)/n:.1f}',
                f'{min(spreads):.1f}',
                f'{max(spreads):.1f}',
                f'{sum(gauges)/n:.1f}',
                f'{sum(bases)/n:.1f}',
            ])

        t = Table(rows, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
        ]))
        return t

    def _zone_property_table(self, props: List[Dict], num_storms: int) -> Table:
        """Build per-property waterfall table for a zone."""
        headers = [
            'Property', 'Dist (m)', 'Offset (m)', 'Floor (m)',
            'Floods', 'Trans %',
            'Gauge (bp)', 'SHD (bp)', 'SHE (bp)', 'Prop (bp)', 'Basis (bp)',
        ]
        rows = [headers]

        for p in props:
            rows.append([
                p['pid'][:16],
                f'{p["dist_m"]:.0f}',
                f'{p["offset"]:.2f}',
                f'{p["floor"]:.2f}',
                str(p['flood_count']),
                f'{p["transmission"]:.1%}',
                f'{p["gauge_spread"]:.1f}',
                f'{p["shd_spread"]:.1f}',
                f'{p["she_spread"]:.1f}',
                f'{p["prop_spread"]:.1f}',
                f'{p["basis"]:+.1f}',
            ])

        col_widths = [105, 50, 55, 45, 45, 45, 55, 55, 55, 55, 55]
        t = Table(rows, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#37474F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDBDBD')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
        ]))
        return t
