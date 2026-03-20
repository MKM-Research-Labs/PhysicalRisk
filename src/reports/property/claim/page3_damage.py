# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Page 3 — Flood Depth & Damage Assessment."""

from collections import defaultdict
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .formatters import fmt_gbp, seq_type_color
from .layouts import body_style, white_hdr_style


def build_page3_damage(
    prop_data: dict,
    prop_record: dict,
    sequence_lookup: Dict[str, dict],
    styles,
) -> List:
    elements: List = []

    elements.append(Paragraph('FLOOD DAMAGE ASSESSMENT', styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1A237E')))
    elements.append(Spacer(1, 0.08 * 72))

    note_data = [[Paragraph(
        '<b>Damage Model Note:</b> Damage is assessed at the maximum flood depth '
        'reached within each storm sequence. In a multi-storm sequence, water '
        'levels remain elevated between storms; accordingly, damage is determined '
        'by the peak water level attained, not the cumulative sum of individual events.',
        styles['NoteBox']
    )]]
    note_tbl = Table(note_data, colWidths=[6.5 * 72])
    note_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#EDE7F6')),
        ('BOX',           (0, 0), (-1, -1), 1,  colors.HexColor('#7B1FA2')),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    elements.append(note_tbl)
    elements.append(Spacer(1, 0.12 * 72))

    flood_events = prop_data.get('flood_events', [])
    valuation = prop_record.get('Valuation', {})
    prop_value = float(valuation.get('PropertyValue', 0) or 0)

    if not flood_events:
        elements.append(Paragraph('No flood events recorded for this property.',
                                  styles['BodyText10']))
        return elements

    # Sequence grouping — worst event per sequence
    seq_groups: Dict[str, List[dict]] = defaultdict(list)
    for event in flood_events:
        seq_id = event.get('sequence_id') or 'isolated'
        seq_groups[seq_id].append(event)

    worst_in_seq: Dict[str, str] = {}
    for seq_id, evts in seq_groups.items():
        worst = max(evts, key=lambda e: e.get('flood_depth_m', 0))
        worst_in_seq[seq_id] = worst.get('storm_id', '')

    # Storm-by-storm damage table
    elements.append(Paragraph('Storm-by-Storm Damage Table', styles['SubSectionHeader']))

    hdr = [
        Paragraph('<b>Storm ID</b>',         white_hdr_style(styles)),
        Paragraph('<b>Seq Type</b>',         white_hdr_style(styles)),
        Paragraph('<b>Depth (m)</b>',        white_hdr_style(styles)),
        Paragraph('<b>Damage Ratio</b>',     white_hdr_style(styles)),
        Paragraph('<b>Damage Amount</b>',    white_hdr_style(styles)),
        Paragraph('<b>Post-Damage Value</b>', white_hdr_style(styles)),
        Paragraph('<b>Worst in Seq?</b>',    white_hdr_style(styles)),
    ]
    col_w = [1.3*72, 0.9*72, 0.75*72, 0.85*72, 1.1*72, 1.1*72, 0.7*72]

    rows2 = [hdr]
    row2_styles: List = []

    for i, event in enumerate(flood_events):
        row_idx = i + 1
        storm_id = event.get('storm_id', 'N/A')
        seq_id = event.get('sequence_id') or 'isolated'
        seq_type = (sequence_lookup.get(seq_id, {}).get('sequence_type', 'isolated')
                    if seq_id != 'isolated' else 'isolated')
        depth = event.get('flood_depth_m', 0.0)
        damage_ratio = event.get('damage_ratio', 0.0)
        damage_amt = prop_value * damage_ratio
        post_val = prop_value - damage_amt
        is_worst = (worst_in_seq.get(seq_id) == storm_id)
        worst_mark = '\u2713' if is_worst else ''

        font = 'Helvetica-Bold' if is_worst else 'Helvetica'
        row_color = seq_type_color(seq_type)
        row2_styles.append(('BACKGROUND', (0, row_idx), (-1, row_idx), row_color))
        if is_worst:
            row2_styles.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))

        rows2.append([
            Paragraph(storm_id[:16],               body_style(styles, font)),
            Paragraph(seq_type.capitalize(),        body_style(styles, font)),
            Paragraph(f'{depth:.3f}',              body_style(styles, font)),
            Paragraph(f'{damage_ratio:.4f}',       body_style(styles, font)),
            Paragraph(fmt_gbp(damage_amt),         body_style(styles, font)),
            Paragraph(fmt_gbp(post_val),           body_style(styles, font)),
            Paragraph(worst_mark,                  body_style(styles, font, align=TA_CENTER)),
        ])

    tbl2 = Table(rows2, colWidths=col_w, repeatRows=1)
    tbl2.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#1B5E20')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ALIGN',         (2, 1), (3, -1),  'CENTER'),
        ('ALIGN',         (6, 0), (6, -1),  'CENTER'),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#B0BEC5')),
        ('BOX',           (0, 0), (-1, -1), 1,   colors.HexColor('#1B5E20')),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ] + row2_styles))
    elements.append(tbl2)
    elements.append(Spacer(1, 0.14 * 72))

    # Sequence-level assessment
    elements.append(Paragraph('Sequence-Level Assessment', styles['SubSectionHeader']))

    seq_hdr = [
        Paragraph('<b>Sequence ID</b>',     white_hdr_style(styles)),
        Paragraph('<b>Type</b>',            white_hdr_style(styles)),
        Paragraph('<b>Storms in Seq</b>',   white_hdr_style(styles)),
        Paragraph('<b>Max Depth (m)</b>',   white_hdr_style(styles)),
        Paragraph('<b>Assessed Damage</b>', white_hdr_style(styles)),
        Paragraph('<b>% of Value</b>',      white_hdr_style(styles)),
    ]
    seq_col_w = [1.3*72, 0.9*72, 0.8*72, 0.9*72, 1.2*72, 0.9*72]
    seq_rows = [seq_hdr]
    seq_row_styles: List = []

    for j, (seq_id, evts) in enumerate(seq_groups.items()):
        row_idx = j + 1
        seq_type_raw = (sequence_lookup.get(seq_id, {}).get('sequence_type', 'isolated')
                        if seq_id != 'isolated' else 'isolated')
        n_storms = len(evts)
        max_d = max((e.get('flood_depth_m', 0) for e in evts), default=0.0)
        max_dam_ratio = max((e.get('damage_ratio', 0) for e in evts), default=0.0)
        assessed_damage = prop_value * max_dam_ratio
        pct_value = (assessed_damage / prop_value * 100) if prop_value > 0 else 0.0

        seq_id_disp = seq_id[:12] if len(seq_id) > 12 else seq_id
        if pct_value > 5.0:
            seq_row_styles.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FFCDD2'))
            )

        seq_rows.append([
            Paragraph(seq_id_disp,             styles['BodyText9']),
            Paragraph(seq_type_raw.capitalize(), styles['BodyText9']),
            Paragraph(str(n_storms),            styles['BodyText9']),
            Paragraph(f'{max_d:.3f}',           styles['BodyText9']),
            Paragraph(fmt_gbp(assessed_damage), styles['BodyText9']),
            Paragraph(f'{pct_value:.2f}%',      styles['BodyText9']),
        ])

    seq_tbl = Table(seq_rows, colWidths=seq_col_w, repeatRows=1)
    seq_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#4A148C')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ALIGN',         (2, 1), (-1, -1), 'CENTER'),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#B0BEC5')),
        ('BOX',           (0, 0), (-1, -1), 1,   colors.HexColor('#4A148C')),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3E5F5')]),
    ] + seq_row_styles))
    elements.append(seq_tbl)
    elements.append(Spacer(1, 0.14 * 72))

    # Summary box
    total_assessed = sum(
        prop_value * max((e.get('damage_ratio', 0) for e in evts), default=0.0)
        for evts in seq_groups.values()
    )
    pct_total = (total_assessed / prop_value * 100) if prop_value > 0 else 0.0

    summary_rows = [
        [Paragraph('<b>Assessed Loss (sum of worst per sequence)</b>', styles['BodyText10']),
         Paragraph(fmt_gbp(total_assessed), styles['BodyText10'])],
        [Paragraph('<b>% of Total Property Value</b>', styles['BodyText10']),
         Paragraph(f'{pct_total:.2f}%', styles['BodyText10'])],
        [Paragraph('<b>Property Value (pre-event)</b>', styles['BodyText10']),
         Paragraph(fmt_gbp(prop_value), styles['BodyText10'])],
    ]
    sum_tbl = Table(summary_rows, colWidths=[4.0 * 72, 2.5 * 72])
    sum_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#FFF3E0')),
        ('BOX',           (0, 0), (-1, -1), 1.5, colors.HexColor('#E65100')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.4, colors.HexColor('#FFCC80')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(sum_tbl)
    return elements
