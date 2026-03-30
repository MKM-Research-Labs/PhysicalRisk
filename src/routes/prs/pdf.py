# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PRS trade PDF generation — _generate_trade_pdf()."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def _generate_trade_pdf(cdm_record: dict, cashflows: list, output_dir: Path) -> Path:
    """Generate a PRS trade confirmation PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def _blue_table_style():
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])

    def _orange_table_style():
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E65100')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#FFF3E0')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])

    ps = cdm_record["PhysicalSwap"]
    header = ps["Header"]
    leg = ps["LegData"]
    schedule = ps["ScheduleData"]
    pricing = ps["Pricing"]
    swap_id = header["SwapID"]

    pdf_path = output_dir / f"{swap_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'PRSTitle', parent=styles['Title'],
        fontSize=18, spaceAfter=6, textColor=colors.HexColor('#1565C0'),
    )
    subtitle_style = ParagraphStyle(
        'PRSSubtitle', parent=styles['Normal'],
        fontSize=10, spaceAfter=16, textColor=colors.grey,
    )
    section_style = ParagraphStyle(
        'PRSSection', parent=styles['Heading2'],
        fontSize=12, spaceBefore=14, spaceAfter=6,
        textColor=colors.HexColor('#1565C0'),
    )
    normal = styles['Normal']

    elements = []

    # Title
    elements.append(Paragraph("PRS Trade Confirmation", title_style))
    elements.append(Paragraph(
        f"{swap_id} | {header.get('ValuationDate', '')} | MKM Research Labs",
        subtitle_style
    ))

    # Trade details table
    elements.append(Paragraph("Trade Details", section_style))

    def fmt_money(v):
        return f"GBP {v:,.2f}"

    ctpy_name = header.get("CounterPartyName") or header.get("CounterParty", "N/A")

    trade_data = [
        ["Field", "Value"],
        ["Swap ID", swap_id],
        ["Counterparty", ctpy_name],
        ["Trade Date", header.get("ValuationDate", "")],
        ["Protection Start", header.get("ProtectionStart", "")],
        ["Maturity", schedule.get("EndDate", "")],
        ["Notional", fmt_money(leg.get("Notional", 0))],
        ["Currency", leg.get("Currency", "GBP")],
        ["Payment Frequency", "Semi-Annual"],
        ["Day Count", leg.get("DayCounter", "ACT/360")],
        ["Trigger Level", pricing.get("TriggerLevel", "").title()],
        ["Catchment", header.get("CatchmentID", "")],
    ]

    t = Table(trade_data, colWidths=[2.5 * inch, 4 * inch])
    t.setStyle(_blue_table_style())
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Pricing summary
    elements.append(Paragraph("Pricing Summary", section_style))

    pricing_data = [
        ["Metric", "Value"],
        ["Running Spread", f"{pricing.get('SpreadBps', 0):.1f} bps"],
        ["Fair Spread", f"{pricing.get('FairSpreadBps', 0):.1f} bps"],
        ["NPV (Buyer)", fmt_money(pricing.get("NPV", 0))],
        ["Premium Leg PV", fmt_money(pricing.get("PremiumLegPV", 0))],
        ["Protection Leg PV", fmt_money(pricing.get("ProtectionLegPV", 0))],
        ["Risky Annuity", f"{pricing.get('RiskyAnnuity', 0):.4f}"],
        ["Risk-Free Rate", f"{pricing.get('RiskFreeRate', 0) * 100:.1f}%"],
        ["Recovery Rate", f"{pricing.get('Recovery', 0) * 100:.0f}%"],
    ]

    t2 = Table(pricing_data, colWidths=[2.5 * inch, 4 * inch])
    t2.setStyle(_blue_table_style())
    elements.append(t2)
    elements.append(Spacer(1, 12))

    # Close-out settlement (if this is a close-out trade)
    close_out_of = header.get("CloseOutOf")
    if close_out_of:
        elements.append(Paragraph("Close-Out Settlement", section_style))

        npv = pricing.get("NPV", 0)
        direction = "Payer" if leg.get("Payer") else "Receiver"
        trade_date_str = header.get("ValuationDate", "")
        settlement_str = "T+2"
        try:
            td_parsed = datetime.strptime(trade_date_str, "%Y-%m-%d")
            settle = td_parsed
            days_added = 0
            while days_added < 2:
                settle += timedelta(days=1)
                if settle.weekday() < 5:
                    days_added += 1
            settlement_str = settle.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

        settle_amount = abs(npv)
        if npv >= 0:
            settle_direction = f"Payable to {header.get('CounterPartyName', 'counterparty')}"
        else:
            settle_direction = f"Receivable from {header.get('CounterPartyName', 'counterparty')}"

        settle_data = [
            ["Field", "Value"],
            ["Original Trade", close_out_of],
            ["Close-Out Direction", direction],
            ["Close-Out Spread", f"{pricing.get('SpreadBps', 0):.1f} bps"],
            ["Net Settlement Amount", fmt_money(settle_amount)],
            ["Settlement Direction", settle_direction],
            ["Settlement Date", settlement_str],
        ]

        t_settle = Table(settle_data, colWidths=[2.5 * inch, 4 * inch])
        t_settle.setStyle(_orange_table_style())
        elements.append(t_settle)
        elements.append(Spacer(1, 12))

    # Close-out settlement on original trade (when trade itself is closed)
    close_out_date = header.get("CloseOutDate")
    if close_out_date and not close_out_of:
        elements.append(Paragraph("Close-Out Settlement", section_style))

        settle_amt = header.get("SettlementAmount", 0)
        settle_dir = header.get("SettlementDirection", "")
        settle_date = header.get("SettlementDate", "T+2")
        close_spread = header.get("CloseOutSpread", 0)
        ctpy_name_local = header.get("CounterPartyName", "counterparty")

        if settle_dir == "Receivable":
            settle_label = f"Receivable from {ctpy_name_local}"
        else:
            settle_label = f"Payable to {ctpy_name_local}"

        settle_data = [
            ["Field", "Value"],
            ["Close-Out Date", close_out_date],
            ["Close-Out Spread", f"{close_spread:.1f} bps"],
            ["Trade Spread", f"{pricing.get('SpreadBps', 0):.1f} bps"],
            ["Net Settlement Amount", fmt_money(settle_amt)],
            ["Settlement Direction", settle_label],
            ["Settlement Date", settle_date],
        ]

        t_settle2 = Table(settle_data, colWidths=[2.5 * inch, 4 * inch])
        t_settle2.setStyle(_orange_table_style())
        elements.append(t_settle2)
        elements.append(Spacer(1, 12))

    # Cashflow schedule (if provided)
    if cashflows:
        elements.append(Paragraph("Cashflow Schedule", section_style))

        cf_header = ["Period", "S(t)", "DF(t)", "Prem CF", "PV Prem", "Prot CF", "PV Prot"]
        cf_rows = [cf_header]

        for cf in cashflows:
            cf_rows.append([
                cf.get("label", ""),
                f"{cf.get('S_t', 0) * 100:.2f}%",
                f"{cf.get('df', 0):.4f}",
                f"{cf.get('premCF', 0):,.2f}",
                f"{cf.get('premPV', 0):,.2f}",
                f"{cf.get('protCF', 0):,.2f}",
                f"{cf.get('protPV', 0):,.2f}",
            ])

        col_w = [0.8 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch]
        t3 = Table(cf_rows, colWidths=col_w)
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(t3)

    # Footer
    elements.append(Spacer(1, 24))
    footer_style = ParagraphStyle(
        'PRSFooter', parent=normal, fontSize=8, textColor=colors.grey,
    )
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "CONFIDENTIAL - For authorized use only | MKM Research Labs",
        footer_style
    ))

    doc.build(elements)
    logger.info("PRS trade PDF: %s", pdf_path)
    return pdf_path
