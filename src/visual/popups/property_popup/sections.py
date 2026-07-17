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

"""Property popup sections — HTML section builders that use a PopupBuilder instance."""

from typing import Any, Dict

from .helpers import calculate_ltv_ratio, extract_term_years, calculate_monthly_payment


def create_property_section(builder, prop: Dict[str, Any], property_id: str,
                            address: Dict[str, Any], coordinates: str,
                            construction_year: Any, property_age_factor: str,
                            property_value: Any, has_rloan: bool) -> str:
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


def create_rloan_section(builder, rloan_info: Dict[str, Any],
                            property_value: Any, flood_risk_level: str) -> str:
    """Create the mortgage information section for the popup."""
    mortgage_header = rloan_info.get('Header', {})
    rloan_financial = rloan_info.get('FinancialTerms', {})
    mortgage_application = rloan_info.get('Application', {})

    if not mortgage_header and 'RLoan' in rloan_info:
        mortgage_header = rloan_info.get('RLoan', {}).get('Header', {})
        rloan_financial = rloan_info.get('RLoan', {}).get('FinancialTerms', {})
        mortgage_application = rloan_info.get('RLoan', {}).get('Application', {})

    mortgage_id = mortgage_header.get('RLoanID', 'N/A')
    lender = mortgage_application.get('MortgageProvider', 'N/A')

    loan_amount = rloan_financial.get('OriginalLoan', 0)
    loan_amount_formatted = builder.format_currency(loan_amount)

    interest_rate = rloan_financial.get('OriginalLendingRate', 0)
    interest_rate_formatted = builder.format_percentage(interest_rate)

    ltv_ratio = calculate_ltv_ratio(loan_amount, property_value, rloan_financial)
    ltv_formatted = builder.format_percentage(ltv_ratio)

    term_years = extract_term_years(rloan_financial, rloan_info)
    term_years_formatted = f"{term_years:.0f}" if isinstance(term_years, (int, float)) else 'N/A'

    monthly_payment = calculate_monthly_payment(
        rloan_financial, loan_amount, interest_rate, term_years
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


