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

"""Page 4 — Mortgage Impact Analysis."""

from collections import defaultdict
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .formatters import fmt_gbp
from .layouts import white_hdr_style
from .styles import PURPLE_TABLE_STYLE
from reports.theme_pdf import pdf_colour


def build_page4_rloan(
    prop_data: dict,
    prop_record: dict,
    rloan_record: Optional[dict],
    sequence_lookup: Dict[str, dict],
    styles,
) -> List:
    elements: List = []

    elements.append(Paragraph('MORTGAGE IMPACT ANALYSIS', styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=1, color=pdf_colour('navy')))
    elements.append(Spacer(1, 0.1 * 72))

    if rloan_record is None:
        elements.append(Spacer(1, 0.5 * 72))
        no_mtg = [[Paragraph(
            'No mortgage registered against this property.',
            ParagraphStyle('NoMortgage',
                           parent=styles['Normal'],
                           fontSize=12,
                           alignment=TA_CENTER,
                           textColor=pdf_colour('blue-grey-dark'))
        )]]
        no_mtg_tbl = Table(no_mtg, colWidths=[6.5 * 72])
        no_mtg_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), pdf_colour('blue-grey-bg')),
            ('BOX',           (0, 0), (-1, -1), 1, pdf_colour('blue-grey-pale')),
            ('TOPPADDING',    (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        elements.append(no_mtg_tbl)
        return elements

    valuation = prop_record.get('Valuation', {})
    prop_value = float(valuation.get('PropertyValue', 0) or 0)

    fin_terms = rloan_record.get('FinancialTerms', {})
    curr_status = rloan_record.get('CurrentStatus', {})
    outstanding_balance = float(
        curr_status.get('OutstandingBalance', fin_terms.get('OriginalBalance', 0)) or 0
    )
    original_ltv_pct = float(fin_terms.get('LTV', 0) or 0)
    remaining_term = fin_terms.get('RemainingTerm', fin_terms.get('OriginalTerm', 'N/A'))

    # Pre-event summary
    pre_rows = [
        [Paragraph('<b>Property Value (pre-event)</b>', styles['BodyText9']),
         Paragraph(fmt_gbp(prop_value), styles['BodyText9'])],
        [Paragraph('<b>Outstanding Balance</b>', styles['BodyText9']),
         Paragraph(fmt_gbp(outstanding_balance), styles['BodyText9'])],
        [Paragraph('<b>Original LTV</b>', styles['BodyText9']),
         Paragraph(f'{original_ltv_pct:.2f}%', styles['BodyText9'])],
        [Paragraph('<b>Remaining Term</b>', styles['BodyText9']),
         Paragraph(str(remaining_term), styles['BodyText9'])],
    ]
    pre_tbl = Table(pre_rows, colWidths=[3.5 * 72, 3.0 * 72])
    pre_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), pdf_colour('ok-bg')),
        ('BOX',           (0, 0), (-1, -1), 1,   pdf_colour('green-dark')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, pdf_colour('green-pale')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(pre_tbl)
    elements.append(Spacer(1, 0.14 * 72))

    # Storm-level post-damage LTV
    elements.append(Paragraph('Post-Damage LTV by Storm Event', styles['SubSectionHeader']))

    flood_events = prop_data.get('flood_events', [])
    ltv_hdr = [
        Paragraph('<b>Storm ID</b>',          white_hdr_style(styles)),
        Paragraph('<b>Seq Type</b>',          white_hdr_style(styles)),
        Paragraph('<b>Depth (m)</b>',         white_hdr_style(styles)),
        Paragraph('<b>Post-Damage Value</b>', white_hdr_style(styles)),
        Paragraph('<b>Post-Damage LTV</b>',   white_hdr_style(styles)),
        Paragraph('<b>Negative Equity?</b>',  white_hdr_style(styles)),
    ]
    ltv_col_w = [1.3*72, 0.9*72, 0.75*72, 1.3*72, 1.15*72, 1.0*72]
    ltv_rows = [ltv_hdr]
    ltv_row_styles: List = []

    for i, event in enumerate(flood_events):
        row_idx = i + 1
        storm_id = event.get('storm_id', 'N/A')
        seq_id = event.get('sequence_id') or 'isolated'
        seq_type = (sequence_lookup.get(seq_id, {}).get('sequence_type', 'isolated')
                    if seq_id != 'isolated' else 'isolated')
        depth = event.get('flood_depth_m', 0.0)
        damage_ratio = event.get('damage_ratio', 0.0)
        post_val = prop_value * (1.0 - damage_ratio)
        post_ltv = (outstanding_balance / post_val * 100) if post_val > 0 else float('inf')
        neg_eq = post_val < outstanding_balance
        neg_eq_str = 'YES' if neg_eq else 'No'

        if neg_eq:
            ltv_row_styles += [
                ('BACKGROUND', (0, row_idx), (-1, row_idx), pdf_colour('danger-line-alt')),
                ('FONTNAME',   (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
                ('TEXTCOLOR',  (5, row_idx), (5, row_idx),  pdf_colour('red-deep')),
            ]

        ltv_rows.append([
            Paragraph(storm_id[:16],   styles['BodyText9']),
            Paragraph(seq_type.capitalize(), styles['BodyText9']),
            Paragraph(f'{depth:.3f}',  styles['BodyText9']),
            Paragraph(fmt_gbp(post_val), styles['BodyText9']),
            Paragraph(f'{post_ltv:.2f}%' if post_ltv < 1000 else '>1000%',
                      styles['BodyText9']),
            Paragraph(neg_eq_str, styles['BodyText9']),
        ])

    ltv_tbl = Table(ltv_rows, colWidths=ltv_col_w, repeatRows=1)
    ltv_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  pdf_colour('navy')),
        ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 8),
        ('ALIGN',          (2, 1), (-1, -1), 'CENTER'),
        ('GRID',           (0, 0), (-1, -1), 0.4, pdf_colour('blue-grey-mist')),
        ('BOX',            (0, 0), (-1, -1), 1,   pdf_colour('navy')),
        ('TOPPADDING',     (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
        ('LEFTPADDING',    (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 4),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, pdf_colour('accent-soft')]),
    ] + ltv_row_styles))
    elements.append(ltv_tbl)
    elements.append(Spacer(1, 0.14 * 72))

    # Sequence-level LTV
    elements.append(Paragraph('Sequence-Level LTV Assessment', styles['SubSectionHeader']))

    seq_groups: Dict[str, List[dict]] = defaultdict(list)
    for event in flood_events:
        sid = event.get('sequence_id') or 'isolated'
        seq_groups[sid].append(event)

    sl_hdr = [
        Paragraph('<b>Sequence ID</b>',      white_hdr_style(styles)),
        Paragraph('<b>Type</b>',             white_hdr_style(styles)),
        Paragraph('<b>Post-Damage LTV</b>',  white_hdr_style(styles)),
        Paragraph('<b>Negative Equity?</b>', white_hdr_style(styles)),
    ]
    sl_col_w = [1.8*72, 1.0*72, 1.5*72, 1.5*72]
    sl_rows = [sl_hdr]
    sl_row_styles: List = []

    for j, (seq_id, evts) in enumerate(seq_groups.items()):
        row_idx = j + 1
        seq_type_raw = (sequence_lookup.get(seq_id, {}).get('sequence_type', 'isolated')
                        if seq_id != 'isolated' else 'isolated')
        worst_evt = max(evts, key=lambda e: e.get('flood_depth_m', 0))
        dam_ratio = worst_evt.get('damage_ratio', 0.0)
        post_v = prop_value * (1.0 - dam_ratio)
        sl_ltv = (outstanding_balance / post_v * 100) if post_v > 0 else float('inf')
        neg = post_v < outstanding_balance
        neg_str = 'YES' if neg else 'No'

        if neg:
            sl_row_styles.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), pdf_colour('danger-line-alt'))
            )

        seq_id_disp = seq_id[:16] if len(seq_id) > 16 else seq_id
        sl_rows.append([
            Paragraph(seq_id_disp,         styles['BodyText9']),
            Paragraph(seq_type_raw.capitalize(), styles['BodyText9']),
            Paragraph(f'{sl_ltv:.2f}%' if sl_ltv < 1000 else '>1000%',
                      styles['BodyText9']),
            Paragraph(neg_str, styles['BodyText9']),
        ])

    sl_tbl = Table(sl_rows, colWidths=sl_col_w, repeatRows=1)
    sl_tbl.setStyle(PURPLE_TABLE_STYLE)
    if sl_row_styles:
        sl_tbl.setStyle(TableStyle(sl_row_styles))
    elements.append(sl_tbl)
    elements.append(Spacer(1, 0.14 * 72))

    # Summary box
    neg_eq_count = sum(
        1 for event in flood_events
        if prop_value * (1.0 - event.get('damage_ratio', 0)) < outstanding_balance
    )
    all_ltvs = []
    for event in flood_events:
        pv = prop_value * (1.0 - event.get('damage_ratio', 0))
        if pv > 0:
            all_ltvs.append(outstanding_balance / pv * 100)
    worst_ltv = max(all_ltvs) if all_ltvs else 0.0

    worst_seq_dam = max(
        (max((e.get('damage_ratio', 0) for e in evts), default=0.0)
         for evts in seq_groups.values()),
        default=0.0
    )
    assessed_post_v = prop_value * (1.0 - worst_seq_dam)
    assessed_ltv = (outstanding_balance / assessed_post_v * 100
                    if assessed_post_v > 0 else float('inf'))

    mtg_sum_rows = [
        [Paragraph('<b>Number of events causing negative equity</b>', styles['BodyText9']),
         Paragraph(str(neg_eq_count), styles['BodyText9'])],
        [Paragraph('<b>Worst post-event LTV (storm-level)</b>', styles['BodyText9']),
         Paragraph(f'{worst_ltv:.2f}%' if worst_ltv < 1000 else '>1000%',
                   styles['BodyText9'])],
        [Paragraph('<b>Assessed post-damage LTV (worst sequence)</b>', styles['BodyText9']),
         Paragraph(f'{assessed_ltv:.2f}%' if assessed_ltv < 1000 else '>1000%',
                   styles['BodyText9'])],
    ]
    mtg_sum_tbl = Table(mtg_sum_rows, colWidths=[4.5 * 72, 2.0 * 72])
    mtg_sum_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), pdf_colour('warn-bg')),
        ('BOX',           (0, 0), (-1, -1), 1.5, pdf_colour('gold-dark')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.4, pdf_colour('warn-line-soft')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(mtg_sum_tbl)
    return elements
