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

"""Commercial-asset marker popup HTML generation.

Minimal first slice: shows CommercialType, address, valuation, a small
set of physical attributes (storeys, area), and a Loan section if
commercial_loan.json has a 1:1 match by PropertyID.
"""

from typing import Any, Dict, Optional

from ...utils import DataFormatter


def create_commercial_popup(asset: Dict[str, Any],
                            loan: Optional[Dict[str, Any]] = None) -> str:
    """Build the popup HTML for a commercial asset marker.

    Args:
        asset: A single CommercialAsset record (the full dict).
        loan:  Optional commercial loan record linked by PropertyID.

    Returns:
        HTML string ready to wrap in folium.Popup.
    """
    ca = asset.get("CommercialAsset", {})
    header = ca.get("Header", {})
    attrs = ca.get("CommercialAttributes", {})
    valuation = ca.get("Valuation", {})
    location = ca.get("Location", {})

    pid = header.get("PropertyID", "Unknown")
    ctype = attrs.get("CommercialType", "Other")
    address_str = (
        f"{location.get('BuildingNumber', '')} {location.get('StreetName', '')}, "
        f"{location.get('TownCity', '')}".strip(", ")
    )
    postcode = location.get("Postcode", "")
    value = valuation.get("PropertyValue", 0)
    area = attrs.get("PropertyAreaSqm", "?")
    storeys = attrs.get("NumberOfStoreys", "?")
    occupancy = attrs.get("OccupancyStatus", "Unknown")
    use_class = attrs.get("UseClassUKO", "")

    content = f"""
        <div style="font-family: Arial; width: 320px; max-height: 400px; overflow-y: auto;">
            <h4 style="margin-bottom: 5px; color: #6C3483;">
                {ctype} &mdash; {pid}
            </h4>
            <p style="color: #6C3483; margin-top: 10px;"><b>Address:</b> {address_str}</p>
            <p style="color: #6C3483; margin-top: 5px;"><b>Postcode:</b> {postcode}</p>

            <div style="background-color: #F5EEF8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #6C3483;">Commercial Asset</h5>
                <p><b>Type:</b> {ctype}</p>
                {f'<p><b>Use Class (UKO):</b> {use_class}</p>' if use_class else ''}
                <p><b>Occupancy:</b> {occupancy}</p>
                <p><b>Gross Internal Area:</b> {area} sqm</p>
                <p><b>Storeys:</b> {storeys}</p>
                <p><b>Capital Value:</b> {DataFormatter.format_currency(value)}</p>
            </div>
    """

    if loan:
        content += _loan_section(loan)

    content += "</div>"
    return content


def _loan_section(loan: Dict[str, Any]) -> str:
    """Render the linked-loan subsection."""
    m = loan.get("Mortgage", {})
    terms = m.get("FinancialTerms", {})
    features = m.get("Features", {})
    status = m.get("CurrentStatus", {})
    app = m.get("Application", {})

    loan_id = m.get("Header", {}).get("MortgageID", "Unknown")
    lender = app.get("MortgageProvider", "Unknown")
    original = terms.get("OriginalLoan", 0)
    outstanding = status.get("OutstandingBalance", 0)
    ltv = terms.get("OriginalLTV", 0)
    rate = terms.get("OriginalLendingRate", 0)
    repayment = features.get("RepaymentType", "Unknown")
    term_months = terms.get("OriginalTerm", 0)
    term_years = term_months // 12 if term_months else "?"

    return f"""
        <div style="background-color: #FDEBD0; padding: 10px; border-radius: 5px; margin-top: 10px;">
            <h5 style="margin-top: 0; color: #6E2C00;">Loan</h5>
            <p><b>Loan ID:</b> {loan_id}</p>
            <p><b>Lender:</b> {lender}</p>
            <p><b>Original:</b> {DataFormatter.format_currency(original)}</p>
            <p><b>Outstanding:</b> {DataFormatter.format_currency(outstanding)}</p>
            <p><b>LTV:</b> {DataFormatter.format_percentage(ltv)}</p>
            <p><b>Rate:</b> {DataFormatter.safe_format_float(rate * 100, 2)}%</p>
            <p><b>Term:</b> {term_years} years &mdash; {repayment}</p>
        </div>
    """
