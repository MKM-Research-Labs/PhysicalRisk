# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Mortgage risk circle popup HTML generation."""

from typing import Any, Dict, Optional

from ...utils import ColorSchemes, DataFormatter


def create_mortgage_circle_popup(location: Dict[str, Any]) -> str:
    """
    Create popup content for mortgage risk circles.

    Args:
        location: Mortgage location data

    Returns:
        HTML string for popup content
    """
    mortgage_info = location['mortgage_info']
    mortgage_risk_info = location['mortgage_risk_info']
    property_flood_info = location['property_flood_info']

    loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
    interest_rate = mortgage_info.get('original_lending_rate', mortgage_info.get('OriginalLendingRate', 0))
    ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))

    popup_content = f"""
        <div style="font-family: Arial; width: 280px;">
            <h4 style="margin-bottom: 5px; color: #8E44AD;">Mortgage Risk Circle</h4>
            <p style="color: #566573; font-size: 0.9em;">Property: {location['property_id']}</p>

            <div style="background-color: #E8DAEF; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #6C3483;">Loan Details</h5>
                <p style="margin: 2px 0;"><b>Amount:</b> {DataFormatter.format_currency(loan_amount)}</p>
                <p style="margin: 2px 0;"><b>Interest Rate:</b> {DataFormatter.safe_format_float(interest_rate * 100 if interest_rate and interest_rate < 1 else interest_rate, 2)}%</p>
                <p style="margin: 2px 0;"><b>LTV Ratio:</b> {DataFormatter.format_percentage(ltv_ratio)}</p>
            </div>
    """

    if mortgage_risk_info:
        mortgage_value = mortgage_risk_info.get('mortgage_value', 0)
        flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')

        popup_content += f"""
            <div style="background-color: #FADBD8; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #943126;">Risk Assessment</h5>
                <p style="margin: 2px 0;"><b>Mortgage Value:</b> {DataFormatter.format_currency(mortgage_value)}</p>
                <p style="margin: 2px 0;"><b>Flood Risk:</b> <span style="color: {ColorSchemes.get_flood_risk_color(flood_risk_level)}; font-weight: bold;">{flood_risk_level}</span></p>
                <p style="margin: 2px 0;"><b>Value at Risk:</b> {DataFormatter.format_currency(mortgage_risk_info.get('mortgage_value_at_risk', 0))}</p>
            </div>
            """

    if property_flood_info:
        popup_content += f"""
            <div style="background-color: #D5F5E3; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #1E8449;">Flood Context</h5>
                <p style="margin: 2px 0;"><b>Flood Depth:</b> {DataFormatter.safe_format_float(property_flood_info.get('flood_depth', 0), 2)} m</p>
                <p style="margin: 2px 0;"><b>Risk Level:</b> {property_flood_info.get('risk_level', 'Unknown')}</p>
            </div>
            """

    popup_content += "</div>"
    return popup_content
