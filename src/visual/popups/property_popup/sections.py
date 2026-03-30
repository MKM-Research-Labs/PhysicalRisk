# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Property popup sections — HTML section builders that use a PopupBuilder instance."""

from typing import Any, Dict, Optional

from .helpers import calculate_ltv_ratio, extract_term_years, calculate_monthly_payment
from .risk import get_mortgage_risk_summary, get_overall_risk_color


def create_property_section(builder, prop: Dict[str, Any], property_id: str,
                            address: Dict[str, Any], coordinates: str,
                            construction_year: Any, property_age_factor: str,
                            property_value: Any, has_mortgage: bool) -> str:
    """Create the property information section for the popup."""
    formatted_address = f"{address.get('building_number', '')} {address.get('street_name', '')}, {address.get('town_city', '')}"
    if address.get('post_code'):
        formatted_address += f", {address['post_code']}"

    value_display = builder.format_currency(property_value)

    prop_header = prop.get('PropertyHeader', {})
    header = prop_header.get('Header', {})
    attributes = prop_header.get('PropertyAttributes', {})
    construction = prop_header.get('Construction', {})

    content = f"""
            {builder.create_data_row("Property Type", header.get('propertyType', 'Unknown'))}
            {builder.create_data_row("Status", header.get('propertyStatus', 'Unknown'))}
            {builder.create_data_row("Building Type", attributes.get('PropertyType', 'Unknown'))}
            {builder.create_data_row("Address", formatted_address)}
            {builder.create_data_row("Coordinates", coordinates)}
            {builder.create_data_row("Construction Year", f"{construction_year} ({property_age_factor})")}
            {builder.create_data_row("Number of Storeys", attributes.get('NumberOfStoreys', 'Unknown'))}
            {builder.create_data_row("Construction Type", construction.get('ConstructionType', 'Unknown'))}
            {builder.create_data_row("Property Value", value_display)}
        """

    return builder.create_section("Property Information", content)


def create_flood_info_section(builder, flood_info: Dict[str, Any]) -> str:
    """Create the flood risk information section for the popup."""
    if not flood_info:
        return ""

    risk_level = flood_info.get('risk_level', 'Unknown')
    risk_color = builder.get_risk_color(risk_level)

    content = f"""
            {builder.create_data_row("Nearest Gauge", flood_info.get('nearest_gauge', 'N/A'))}
            {builder.create_data_row("Distance to Gauge", f"{builder.safe_format_float(flood_info.get('distance_to_gauge', 'N/A'))} km")}
            {builder.create_data_row("Water Level", f"{builder.safe_format_float(flood_info.get('water_level', 'N/A'))} m")}
            {builder.create_data_row("Flood Depth", f"{builder.safe_format_float(flood_info.get('flood_depth', 'N/A'))} m")}
            {builder.create_data_row("Risk Value", flood_info.get('risk_value', 'N/A'))}
            {builder.create_data_row("Risk Level", builder.create_colored_text(risk_level, risk_color, bold=True))}
            {builder.create_data_row("Value at Risk", builder.format_currency(flood_info.get('value_at_risk', 'N/A')))}
        """

    return builder.create_section("Detailed Flood Risk Information", content, "#D5F5E3", "#1E8449")


def create_mortgage_section(builder, mortgage_info: Dict[str, Any],
                            property_value: Any, flood_risk_level: str) -> str:
    """Create the mortgage information section for the popup."""
    mortgage_header = mortgage_info.get('Header', {})
    mortgage_financial = mortgage_info.get('FinancialTerms', {})
    mortgage_application = mortgage_info.get('Application', {})

    if not mortgage_header and 'Mortgage' in mortgage_info:
        mortgage_header = mortgage_info.get('Mortgage', {}).get('Header', {})
        mortgage_financial = mortgage_info.get('Mortgage', {}).get('FinancialTerms', {})
        mortgage_application = mortgage_info.get('Mortgage', {}).get('Application', {})

    mortgage_id = mortgage_header.get('MortgageID', 'N/A')
    lender = mortgage_application.get('MortgageProvider', 'N/A')

    loan_amount = mortgage_financial.get('OriginalLoan', 0)
    loan_amount_formatted = builder.format_currency(loan_amount)

    interest_rate = mortgage_financial.get('OriginalLendingRate', 0)
    interest_rate_formatted = builder.format_percentage(interest_rate)

    ltv_ratio = calculate_ltv_ratio(loan_amount, property_value, mortgage_financial)
    ltv_formatted = builder.format_percentage(ltv_ratio)

    term_years = extract_term_years(mortgage_financial, mortgage_info)
    term_years_formatted = f"{term_years:.0f}" if isinstance(term_years, (int, float)) else 'N/A'

    monthly_payment = calculate_monthly_payment(
        mortgage_financial, loan_amount, interest_rate, term_years
    )
    monthly_payment_formatted = builder.format_currency(monthly_payment)

    content = f"""
            {builder.create_data_row("Mortgage ID", mortgage_id)}
            {builder.create_data_row("Lender", lender)}
            {builder.create_data_row("Loan Amount", loan_amount_formatted)}
            {builder.create_data_row("Interest Rate", interest_rate_formatted)}
            {builder.create_data_row("Term", f"{term_years_formatted} years")}
            {builder.create_data_row("Monthly Payment", monthly_payment_formatted)}
            {builder.create_data_row("LTV Ratio", ltv_formatted)}
        """

    header_html = """
        <div style="margin-top: 20px; border-top: 3px solid #8E44AD; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #8E44AD; text-align: center; background-color: #E8DAEF; padding: 5px; border-radius: 5px;">MORTGAGE DETAILS</h4>
        """

    section_html = builder.create_section("Loan Information", content, "#E8DAEF", "#6C3483")

    return header_html + section_html + "</div>"


def create_mortgage_risk_section(builder, mortgage_risk_info: Dict[str, Any]) -> str:
    """Create the mortgage risk analysis section for the popup."""
    if not mortgage_risk_info:
        return ""

    loan_amount = mortgage_risk_info.get('loan_amount', 0)
    interest_rate = mortgage_risk_info.get('interest_rate', 0)
    monthly_payment = mortgage_risk_info.get('monthly_payment', 0)
    annual_payment = mortgage_risk_info.get('annual_payment', 0)
    credit_spread = mortgage_risk_info.get('credit_spread', 0)
    recovery_haircut = mortgage_risk_info.get('recovery_haircut', 0)
    mortgage_value = mortgage_risk_info.get('mortgage_value', 0)
    mortgage_value_at_risk = mortgage_risk_info.get('mortgage_value_at_risk', 0)
    flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
    flood_risk_value = mortgage_risk_info.get('flood_risk_value', 0)
    flood_depth = mortgage_risk_info.get('flood_depth', 0)
    property_value = mortgage_risk_info.get('property_value', 0)

    ltv_ratio = 0
    if isinstance(loan_amount, (int, float)) and isinstance(property_value, (int, float)) and property_value > 0:
        ltv_ratio = loan_amount / property_value

    mortgage_details_content = f"""
            {builder.create_data_row("Mortgage ID", mortgage_risk_info.get('MortgageID', 'N/A'))}
            {builder.create_data_row("Loan Amount", builder.format_currency(loan_amount))}
            {builder.create_data_row("Interest Rate", builder.format_percentage(interest_rate))}
            {builder.create_data_row("Monthly Payment", builder.format_currency(monthly_payment))}
            {builder.create_data_row("Annual Payment", builder.format_currency(annual_payment))}
            {builder.create_data_row("Property Value", builder.format_currency(property_value))}
            {builder.create_data_row("LTV Ratio", builder.format_percentage(ltv_ratio))}
        """

    risk_metrics_content = f"""
            {builder.create_data_row("Credit Spread", builder.format_percentage(credit_spread))}
            {builder.create_data_row("Recovery Haircut", builder.format_percentage(recovery_haircut))}
            {builder.create_data_row("Mortgage Value", builder.format_currency(mortgage_value))}
            {builder.create_data_row("Mortgage Value at Risk", builder.format_currency(mortgage_value_at_risk))}
            {builder.create_data_row("Flood Risk Level", builder.create_colored_text(flood_risk_level, builder.get_risk_color(flood_risk_level), bold=True))}
            {builder.create_data_row("Flood Risk Value", builder.format_percentage(flood_risk_value))}
            {builder.create_data_row("Flood Depth", f"{builder.safe_format_float(flood_depth)} m")}
        """

    risk_summary = get_mortgage_risk_summary(flood_risk_level, mortgage_value, loan_amount, ltv_ratio)
    risk_color = get_overall_risk_color(flood_risk_level, mortgage_value, loan_amount, ltv_ratio)

    impact_assessment_content = f"""
            {builder.create_data_row("Overall Assessment", builder.create_colored_text(risk_summary, risk_color, bold=True))}
        """

    header_html = """
        <div style="margin-top: 20px; border-top: 3px solid #5DADE2; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #2E86C1; text-align: center; background-color: #D6EAF8; padding: 5px; border-radius: 5px;">MORTGAGE RISK ANALYSIS</h4>
        """

    details_section = builder.create_section("Mortgage Details", mortgage_details_content, "#D6EAF8", "#2874A6")
    risk_section = builder.create_section("Risk Metrics", risk_metrics_content, "#FCF3CF", "#B7950B")
    impact_section = builder.create_section("Impact Assessment", impact_assessment_content, "#FADBD8", "#943126")

    return header_html + details_section + risk_section + impact_section + "</div>"
