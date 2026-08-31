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

"""Page 1 — Claim Cover Sheet."""

from datetime import datetime
from typing import List, Optional

from reportlab.lib import colors
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from config.format import property_title_py
from .formatters import fmt_gbp
from reports.theme_pdf import pdf_colour


def build_page1_cover(
    prop_data: dict,
    prop_record: dict,
    rloan_record: Optional[dict],
    claim_ref: str,
    today: datetime,
    styles,
) -> List:
    elements: List = []
    prop_id = prop_data.get('property_id', 'UNKNOWN')

    elements.append(Spacer(1, 0.3 * 72))

    elements.append(Paragraph('FLOOD DAMAGE ASSESSMENT REPORT', styles['ClaimTitle']))
    elements.append(Paragraph('Insurance Claim Documentation', styles['ClaimSubTitle']))
    elements.append(Spacer(1, 0.12 * 72))

    # Claim reference banner
    banner_data = [[Paragraph(f'CLAIM REFERENCE: {claim_ref}', styles['ClaimRefBanner'])]]
    banner_table = Table(banner_data, colWidths=[6.5 * 72])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, -1), pdf_colour('red-dark')),
        ('TOPPADDING',     (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 8),
        ('LEFTPADDING',    (0, 0), (-1, -1), 12),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 12),
        ('BOX',            (0, 0), (-1, -1), 1.5, pdf_colour('red-deep')),
    ]))
    elements.append(banner_table)
    elements.append(Spacer(1, 0.2 * 72))

    # Two-column info box
    location = prop_data.get('location', {})
    lat = location.get('latitude', 'N/A')
    lon = location.get('longitude', 'N/A')
    loc_str = f"{lat:.5f}, {lon:.5f}" if isinstance(lat, float) else f"{lat}, {lon}"

    header = prop_record.get('Header', {})
    valuation = prop_record.get('Valuation', {})
    attributes = prop_record.get('PropertyAttributes', {})
    construction = prop_record.get('Construction', {})

    catchment = header.get('catchment', 'Thames')
    prop_type = prop_data.get('property_type', attributes.get('PropertyType', 'N/A'))
    con_year = prop_data.get('construction_year', construction.get('ConstructionYear', 'N/A'))
    flood_zone = prop_data.get('flood_zone', 'N/A')
    elevation = prop_data.get('elevation_m', 'N/A')
    floor_level = prop_data.get('floor_level_m', 'N/A')

    elev_str = f"{elevation:.2f} m" if isinstance(elevation, float) else str(elevation)
    floor_str = f"{floor_level:.2f} m" if isinstance(floor_level, float) else str(floor_level)

    claim_loc = prop_record.get('Location', {})
    claim_addr = f"{claim_loc.get('BuildingNumber', '')} {claim_loc.get('StreetName', '')}".strip()
    prop_label = property_title_py(claim_addr, prop_id)

    left_col = [
        ('Property', prop_label),
        ('Property Type', str(prop_type)),
        ('Construction Year', str(con_year)),
        ('Flood Zone', str(flood_zone)),
        ('Location (lat, lon)', loc_str),
    ]
    right_col = [
        ('Report Date', today.strftime('%Y-%m-%d')),
        ('Assessment Date', today.strftime('%Y-%m-%d')),
        ('Catchment', catchment),
        ('Ground Level', elev_str),
        ('Floor Level', floor_str),
    ]

    info_rows = []
    for (lk, lv), (rk, rv) in zip(left_col, right_col):
        info_rows.append([
            Paragraph(f'<b>{lk}:</b> {lv}', styles['BodyText9']),
            Paragraph(f'<b>{rk}:</b> {rv}', styles['BodyText9']),
        ])

    info_table = Table(info_rows, colWidths=[3.25 * 72, 3.25 * 72])
    info_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), pdf_colour('accent-soft')),
        ('BOX',           (0, 0), (-1, -1), 1,   pdf_colour('accent-mid')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, pdf_colour('accent-pale')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2 * 72))

    # Summary stats box
    flood_events = prop_data.get('flood_events', [])
    total_events = len(flood_events)
    max_depth = max((e.get('flood_depth_m', 0) for e in flood_events), default=0.0)
    max_damage = max((e.get('damage_ratio', 0) for e in flood_events), default=0.0)
    mortgage_impacted = 'Yes' if rloan_record else 'No'

    summary_data = [
        [
            Paragraph('<b>Total Flood Events</b>', styles['BodyText10']),
            Paragraph('<b>Max Flood Depth</b>',    styles['BodyText10']),
            Paragraph('<b>Max Damage Ratio</b>',   styles['BodyText10']),
            Paragraph('<b>Mortgage Impacted</b>',  styles['BodyText10']),
        ],
        [
            Paragraph(str(total_events),         styles['ClaimTitle']),
            Paragraph(f'{max_depth:.2f} m',      styles['ClaimTitle']),
            Paragraph(f'{max_damage:.1%}',        styles['ClaimTitle']),
            Paragraph(mortgage_impacted,          styles['ClaimTitle']),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[1.625 * 72] * 4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  pdf_colour('navy-mid')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('BACKGROUND',    (0, 1), (-1, -1), pdf_colour('sunken')),
        ('BOX',           (0, 0), (-1, -1), 1.5, pdf_colour('navy')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.5, pdf_colour('grey')),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25 * 72))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=pdf_colour('blue-grey-pale')))
    elements.append(Spacer(1, 0.1 * 72))
    elements.append(Paragraph(
        'This report is generated from MKM Physical Risk Platform flood simulation data.',
        styles['FooterNote']
    ))
    return elements
