# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Property marker popup HTML generation."""

from typing import Any, Dict

from config.format import property_title_py
from ...utils import ColorSchemes, DataFormatter


def create_property_popup(property_info: Dict[str, Any], property_flood_info: Dict[str, Any],
                          has_rloan: bool, mortgage_info: Dict[str, Any]) -> str:
    """Create detailed popup content for a property marker."""
    property_id = property_info['property_id']
    address = property_info.get('address', {})
    valuation = property_info.get('valuation', {})

    prop_address = f"{address.get('building_number', '')} {address.get('street_name', '')}".strip()
    prop_label = property_title_py(prop_address, property_id)
    address_str = f"{address.get('street', 'N/A')}, {address.get('city', 'N/A')}, {address.get('postcode', 'N/A')}"
    property_value = valuation.get('current_value', valuation.get('market_value', 0))

    elevation = property_info.get('ground_elevation', 'N/A')
    floor_level = property_info.get('floor_level_m', 'N/A')
    flood_zone = property_info.get('flood_zone', 'N/A')
    postcode = address.get('post_code', address.get('postcode', 'N/A'))
    coords = property_info.get('coordinates', {})
    coord_lat = coords.get('latitude')
    coord_lon = coords.get('longitude')
    coord_str = f"{coord_lat:.4f}N, {coord_lon:.4f}E" if coord_lat and coord_lon else "N/A"
    river_dist = property_info.get('river_distance_m', 'N/A')
    river_dist_str = f"{float(river_dist):.0f}" if river_dist != 'N/A' and river_dist is not None else "N/A"

    popup_content = f"""
        <div style="font-family: Arial; width: 320px; max-height: 400px; overflow-y: auto;">
            <h4 style="margin-bottom: 5px; color: #1a5276;">{prop_label}</h4>
            <p style="color: #2874A6; margin-top: 10px;"><b>Address:</b> {address_str}</p>
            <p style="color: #2874A6; margin-top: 5px;"><b>Postcode:</b> {postcode}</p>

            <div style="background-color: #EBF5FB; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #1a5276;">Property Details</h5>
                <p><b>Type:</b> {property_info.get('property_type', 'N/A')}</p>
                <p><b>Building:</b> {property_info.get('building_type', 'N/A')}</p>
                <p><b>Construction:</b> {property_info.get('construction_type', 'N/A')}</p>
                <p><b>Build Year:</b> {property_info.get('construction_year', 'N/A')}</p>
                <p><b>Storeys:</b> {property_info.get('number_of_storeys', 'N/A')}</p>
                <p><b>Current Value:</b> {DataFormatter.format_currency(property_value)}</p>
            </div>

            <div style="background-color: #FEF9E7; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #7D6608;">Elevation &amp; Flood Zone</h5>
                <p><b>Ground Elevation:</b> {DataFormatter.safe_format_float(elevation) if elevation != 'N/A' else 'N/A'} m AOD</p>
                <p><b>Floor Level:</b> {DataFormatter.safe_format_float(floor_level) if floor_level != 'N/A' else 'N/A'} m</p>
                <p><b>Flood Zone:</b> {flood_zone}</p>
                <p><b>River Distance:</b> {river_dist_str} m</p>
                <p><b>Coordinates:</b> {coord_str}</p>
            </div>
    """

    if has_rloan and mortgage_info:
        popup_content += create_mortgage_section(mortgage_info, property_value)

    popup_content += "</div>"
    return popup_content


def create_flood_risk_section(property_flood_info: Dict[str, Any]) -> str:
    """Create the flood risk information section."""
    risk_level = property_flood_info.get('risk_level', 'Unknown')
    risk_color = ColorSchemes.get_flood_risk_color(risk_level)

    return f"""
        <div style="background-color: #FEF9E7; padding: 10px; border-radius: 5px; margin-top: 10px;">
            <h5 style="margin-top: 0; color: #7D6608;">Flood Risk Assessment</h5>
            <p><b>Property Elevation:</b> {DataFormatter.safe_format_float(property_flood_info.get('property_elevation', 0), 2)} m</p>
            <p><b>Water Level:</b> {DataFormatter.safe_format_float(property_flood_info.get('water_level', 0), 2)} m</p>
            <p><b>Flood Depth:</b> {DataFormatter.safe_format_float(property_flood_info.get('flood_depth', 0), 2)} m</p>
            <p><b>Risk Level:</b> <span style="color: {risk_color}; font-weight: bold;">{risk_level}</span></p>
            <p><b>Value at Risk:</b> {DataFormatter.format_currency(property_flood_info.get('value_at_risk', 0))}</p>
        </div>
        """


def create_mortgage_section(mortgage_info: Dict[str, Any], property_value: Any) -> str:
    """Create the mortgage information section."""
    loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
    interest_rate = mortgage_info.get('original_lending_rate', mortgage_info.get('OriginalLendingRate', 0))
    term_years = mortgage_info.get('term_years', mortgage_info.get('TermYears', 'N/A'))
    provider = mortgage_info.get('mortgage_provider', mortgage_info.get('MortgageProvider', 'N/A'))

    ltv_ratio = 0
    if loan_amount and property_value:
        try:
            ltv_ratio = float(loan_amount) / float(property_value)
        except (ValueError, TypeError, ZeroDivisionError):
            ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))

    return f"""
        <div style="margin-top: 20px; border-top: 3px solid #8E44AD; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #8E44AD; text-align: center; background-color: #E8DAEF; padding: 5px; border-radius: 5px;">MORTGAGE DETAILS</h4>

            <div style="background-color: #E8DAEF; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #6C3483;">Loan Information</h5>
                <p><b>Lender:</b> {provider}</p>
                <p><b>Loan Amount:</b> {DataFormatter.format_currency(loan_amount)}</p>
                <p><b>Interest Rate:</b> {DataFormatter.safe_format_float(interest_rate * 100 if interest_rate and interest_rate < 1 else interest_rate, 2)}%</p>
                <p><b>Term:</b> {term_years} years</p>
                <p><b>LTV Ratio:</b> {DataFormatter.format_percentage(ltv_ratio)}</p>
            </div>
        </div>
        """


