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

"""Page 2 — Storm Event Chronology."""

from collections import defaultdict
from typing import Dict, List

from reportlab.lib import colors
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .formatters import seq_type_color
from .layouts import body_style, white_hdr_style
from reports.theme_pdf import pdf_colour


def build_page2_chronology(
    prop_data: dict,
    sequence_lookup: Dict[str, dict],
    styles,
) -> List:
    elements: List = []

    elements.append(Paragraph('STORM EVENT CHRONOLOGY', styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=1, color=pdf_colour('navy')))
    elements.append(Spacer(1, 0.1 * 72))

    elements.append(Paragraph(
        'The following table lists all storm events affecting this property in '
        'chronological order. Sequence type indicates whether the storm occurred '
        'as an isolated event or as part of a multi-storm sequence '
        '(doublet: 2 storms, cluster: 3\u20134 storms, persistent: 4+ storms) '
        'within a 168-hour event window.',
        styles['BodyText9']
    ))
    elements.append(Spacer(1, 0.1 * 72))

    flood_events = prop_data.get('flood_events', [])

    if not flood_events:
        elements.append(Paragraph('No flood events recorded for this property.',
                                  styles['BodyText10']))
        return elements

    max_depth_val = max((e.get('flood_depth_m', 0) for e in flood_events), default=0.0)

    col_hdrs = [
        Paragraph('<b>Storm ID</b>',       white_hdr_style(styles)),
        Paragraph('<b>Sequence ID</b>',    white_hdr_style(styles)),
        Paragraph('<b>Seq Type</b>',       white_hdr_style(styles)),
        Paragraph('<b>Flood Depth (m)</b>', white_hdr_style(styles)),
        Paragraph('<b>Damage Ratio</b>',   white_hdr_style(styles)),
        Paragraph('<b>Flooded?</b>',       white_hdr_style(styles)),
        Paragraph('<b>Arrival (hrs)</b>',  white_hdr_style(styles)),
        Paragraph('<b>Peak (hrs)</b>',     white_hdr_style(styles)),
    ]
    col_widths = [1.3*72, 1.1*72, 0.85*72, 0.95*72, 0.85*72, 0.65*72, 0.8*72, 0.7*72]

    rows = [col_hdrs]
    row_styles: List = []
    type_counts: Dict[str, int] = defaultdict(int)

    for i, event in enumerate(flood_events):
        row_idx = i + 1
        storm_id = event.get('storm_id', 'N/A')
        seq_id = event.get('sequence_id', '')
        seq_type = (sequence_lookup.get(seq_id, {}).get('sequence_type', 'isolated')
                    if seq_id else 'isolated')
        depth = event.get('flood_depth_m', 0.0)
        damage_ratio = event.get('damage_ratio', 0.0)
        flooded = 'Yes' if event.get('flooded', depth > 0) else 'No'
        arrival = event.get('arrival_time_hrs', event.get('arrival_hrs', 'N/A'))
        peak = event.get('peak_time_hrs', event.get('peak_hrs', 'N/A'))

        type_counts[seq_type] += 1
        is_worst = abs(depth - max_depth_val) < 1e-9
        font = 'Helvetica-Bold' if is_worst else 'Helvetica'
        row_color = seq_type_color(seq_type)

        row_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), row_color))
        if is_worst:
            row_styles.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))

        storm_id_short = storm_id[:16] if len(storm_id) > 16 else storm_id
        seq_id_short = (seq_id[:12] if seq_id and len(seq_id) > 12
                        else (seq_id or '\u2014'))
        arrival_str = f'{arrival:.1f}' if isinstance(arrival, float) else str(arrival)
        peak_str = f'{peak:.1f}' if isinstance(peak, float) else str(peak)

        rows.append([
            Paragraph(storm_id_short,            body_style(styles, font)),
            Paragraph(seq_id_short,              body_style(styles, font)),
            Paragraph(seq_type.capitalize(),     body_style(styles, font)),
            Paragraph(f'{depth:.3f}',            body_style(styles, font)),
            Paragraph(f'{damage_ratio:.3f}',     body_style(styles, font)),
            Paragraph(flooded,                   body_style(styles, font)),
            Paragraph(arrival_str,               body_style(styles, font)),
            Paragraph(peak_str,                  body_style(styles, font)),
        ])

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  pdf_colour('navy')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('ALIGN',         (3, 1), (4, -1),  'CENTER'),
        ('ALIGN',         (5, 1), (-1, -1), 'CENTER'),
        ('GRID',          (0, 0), (-1, -1), 0.4, pdf_colour('blue-grey-mist')),
        ('BOX',           (0, 0), (-1, -1), 1,   pdf_colour('navy')),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ] + row_styles))
    elements.append(tbl)
    elements.append(Spacer(1, 0.12 * 72))

    stats_parts = [
        f"Isolated: {type_counts.get('isolated', 0)}",
        f"Doublet: {type_counts.get('doublet', 0)}",
        f"Cluster: {type_counts.get('cluster', 0)}",
        f"Persistent: {type_counts.get('persistent', 0)}",
        f"Total Events: {len(flood_events)}",
    ]
    elements.append(Paragraph('  \u2502  '.join(stats_parts), styles['StatsBar']))
    return elements
