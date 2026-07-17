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

"""Page 5 — Claim Determination."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .formatters import fmt_gbp


def build_page5_determination(
    prop_data: dict,
    prop_record: dict,
    rloan_record: Optional[dict],
    sequence_lookup: Dict[str, dict],
    claim_ref: str,
    today: datetime,
    styles,
) -> List:
    elements: List = []

    elements.append(Paragraph('CLAIM DETERMINATION', styles['SectionHeader']))
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1A237E')))
    elements.append(Spacer(1, 0.1 * 72))

    prop_id = prop_data.get('property_id', 'UNKNOWN')

    # Reference box
    ref_rows = [
        [Paragraph('<b>Claim Reference</b>', styles['BodyText9']),
         Paragraph(claim_ref, styles['BodyText9'])],
        [Paragraph('<b>Property ID</b>', styles['BodyText9']),
         Paragraph(prop_id, styles['BodyText9'])],
        [Paragraph('<b>Report Date</b>', styles['BodyText9']),
         Paragraph(today.strftime('%Y-%m-%d'), styles['BodyText9'])],
    ]
    ref_tbl = Table(ref_rows, colWidths=[2.5 * 72, 4.0 * 72])
    ref_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#E8EAF6')),
        ('BOX',           (0, 0), (-1, -1), 1.5, colors.HexColor('#1A237E')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, colors.HexColor('#9FA8DA')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(ref_tbl)
    elements.append(Spacer(1, 0.14 * 72))

    # Assessed losses
    elements.append(Paragraph('Assessed Losses', styles['SubSectionHeader']))

    valuation = prop_record.get('Valuation', {})
    prop_value = float(valuation.get('PropertyValue', 0) or 0)

    flood_events = prop_data.get('flood_events', [])
    seq_groups: Dict[str, List[dict]] = defaultdict(list)
    for event in flood_events:
        sid = event.get('sequence_id') or 'isolated'
        seq_groups[sid].append(event)

    total_assessed = sum(
        prop_value * max((e.get('damage_ratio', 0) for e in evts), default=0.0)
        for evts in seq_groups.values()
    )
    post_damage_value = prop_value - total_assessed

    det_rows: List = [
        ['Property Value (pre-event)',                    fmt_gbp(prop_value)],
        ['Total Assessed Damage (sum of worst per sequence)', fmt_gbp(total_assessed)],
        ['Post-Damage Value',                             fmt_gbp(post_damage_value)],
    ]

    outstanding_balance: Optional[float] = None
    if rloan_record is not None:
        fin_terms = rloan_record.get('FinancialTerms', {})
        curr_status = rloan_record.get('CurrentStatus', {})
        outstanding_balance = float(
            curr_status.get('OutstandingBalance',
                            fin_terms.get('OriginalBalance', 0)) or 0
        )
        post_ltv = (outstanding_balance / post_damage_value * 100
                    if post_damage_value > 0 else float('inf'))
        neg_equity = post_damage_value < outstanding_balance

        det_rows.append(['Outstanding Mortgage', fmt_gbp(outstanding_balance)])
        det_rows.append(['Mortgage LTV (post-damage)',
                         f'{post_ltv:.2f}%' if post_ltv < 1000 else '>1000%'])
        det_rows.append(['Negative Equity', 'YES' if neg_equity else 'No'])

    det_table_data = [[
        Paragraph('<b>Item</b>',
                  ParagraphStyle('DetHdr', parent=styles['Normal'],
                                 fontSize=9, fontName='Helvetica-Bold',
                                 textColor=colors.white)),
        Paragraph('<b>Amount / Value</b>',
                  ParagraphStyle('DetHdr2', parent=styles['Normal'],
                                 fontSize=9, fontName='Helvetica-Bold',
                                 textColor=colors.white, alignment=TA_RIGHT)),
    ]]
    det_row_styles: List = []
    for k, (label, val_str) in enumerate(det_rows):
        row_idx = k + 1
        is_damage = label.startswith('Total Assessed')
        is_neg = label == 'Negative Equity' and val_str == 'YES'

        if is_damage:
            det_row_styles.append(
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FFCDD2'))
            )
        elif is_neg:
            det_row_styles += [
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FF8A80')),
                ('TEXTCOLOR',  (0, row_idx), (-1, row_idx), colors.HexColor('#B71C1C')),
                ('FONTNAME',   (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
            ]

        det_table_data.append([
            Paragraph(label, styles['BodyText9']),
            Paragraph(val_str,
                      ParagraphStyle('DetVal', parent=styles['Normal'],
                                     fontSize=9, alignment=TA_RIGHT)),
        ])

    det_tbl = Table(det_table_data, colWidths=[4.5 * 72, 2.0 * 72])
    det_tbl.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#37474F')),
        ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 9),
        ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#B0BEC5')),
        ('BOX',            (0, 0), (-1, -1), 1.5, colors.HexColor('#37474F')),
        ('TOPPADDING',     (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
        ('LEFTPADDING',    (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
        ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.white, colors.HexColor('#ECEFF1')]),
    ] + det_row_styles))
    elements.append(det_tbl)
    elements.append(Spacer(1, 0.16 * 72))

    # Assessment basis
    elements.append(Paragraph(
        'This assessment is based on depth-damage curves (MKM-DD-001) applied to '
        'peak flood depths at the property location. Flood depths are derived from '
        'IDW interpolation of gauge water surface elevations, attenuated for '
        'distance. Damage model: max depth within each 168-hour event window.',
        styles['BodyText9']
    ))
    elements.append(Spacer(1, 0.18 * 72))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#CFD8DC')))
    elements.append(Spacer(1, 0.12 * 72))

    # Signature block
    sig_lines = [
        ('Prepared by:',     'MKM Physical Risk Platform'),
        ('Model Version:',   'MKM-DD-001 v2.0 / MKM-SS-001 v2.0'),
        ('Report generated:', today.strftime('%Y-%m-%d %H:%M:%S')),
        ('Status:',          'DRAFT \u2014 For review by licensed assessor'),
    ]
    for label, value in sig_lines:
        elements.append(Paragraph(f'<b>{label}</b>  {value}', styles['SignatureLine']))

    elements.append(Spacer(1, 0.18 * 72))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#CFD8DC')))
    elements.append(Spacer(1, 0.08 * 72))

    # Disclaimer
    elements.append(Paragraph(
        'This report is generated from stochastic flood simulation data for risk '
        'assessment purposes. It does not constitute a binding insurance assessment. '
        'All figures are model estimates subject to uncertainty.',
        styles['Disclaimer']
    ))
    return elements
