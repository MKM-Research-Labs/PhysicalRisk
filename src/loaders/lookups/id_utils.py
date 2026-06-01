# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
ID extraction and relationship analysis utilities.
"""

from typing import Any, Dict, Optional, Set


def extract_property_ids(property_data: Optional[Dict[str, Any]]) -> Set[str]:
    """Extract all property IDs from property data."""
    if not property_data:
        return set()

    ids = set()
    for prop in property_data.get("items", []):
        prop_id = prop.get("PropertyHeader", {}).get("Header", {}).get("PropertyID")
        if prop_id:
            ids.add(prop_id)
    return ids


def extract_rloan_ids(rloan_data: Optional[Dict[str, Any]]) -> Set[str]:
    """Extract all loan IDs from loan data."""
    if not rloan_data:
        return set()

    ids = set()
    for loan in rloan_data.get("items", []):
        loan_id = loan.get("RLoan", {}).get("Header", {}).get("RLoanID")
        if loan_id:
            ids.add(loan_id)
    return ids


def extract_rloan_property_ids(rloan_data: Optional[Dict[str, Any]]) -> Set[str]:
    """Extract property IDs referenced in loan data."""
    if not rloan_data:
        return set()

    ids = set()
    for loan in rloan_data.get("items", []):
        prop_id = loan.get("RLoan", {}).get("Header", {}).get("PropertyID")
        if prop_id:
            ids.add(prop_id)
    return ids


def extract_gauge_ids(gauge_data: Optional[Dict[str, Any]]) -> Set[str]:
    """Extract all gauge IDs from gauge data."""
    if not gauge_data:
        return set()

    ids = set()
    gauges = gauge_data.get("items", [])
    for gauge in gauges:
        gauge_id = gauge.get("FloodGauge", {}).get("Header", {}).get("GaugeID")
        if gauge_id:
            ids.add(gauge_id)
    return ids


def analyze_id_relationships(
    property_data: Optional[Dict[str, Any]] = None,
    rloan_data: Optional[Dict[str, Any]] = None,
    flood_risk_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze relationships between IDs in different datasets.

    Returns:
        Dictionary with ID counts and overlap statistics
    """
    property_ids = extract_property_ids(property_data)
    loan_property_ids = extract_rloan_property_ids(rloan_data)
    loan_ids = extract_rloan_ids(rloan_data)

    # Extract IDs from flood risk data (gaugehc.json has hazard_curves key)
    flood_property_ids = set()
    if flood_risk_data:
        # Property IDs from property hazard curves
        flood_property_ids = set(flood_risk_data.get("property_hazard_curves", {}).keys())
        # Also check legacy format
        if not flood_property_ids:
            flood_property_ids = set(flood_risk_data.get("property_risk", {}).keys())

    # Loans with flood risk = loans whose property has flood risk
    flood_loan_ids = set()
    if rloan_data and flood_property_ids:
        for loan in rloan_data.get("items", []):
            hdr = loan.get("RLoan", {}).get("Header", {})
            prop_id = hdr.get("PropertyID")
            loan_id = hdr.get("RLoanID")
            if prop_id in flood_property_ids and loan_id:
                flood_loan_ids.add(loan_id)

    return {
        "counts": {
            "properties": len(property_ids),
            "loans": len(loan_ids),
            "loan_properties": len(loan_property_ids),
            "flood_properties": len(flood_property_ids),
            "flood_loans": len(flood_loan_ids),
        },
        "overlaps": {
            "properties_with_loans": len(property_ids & loan_property_ids),
            "properties_with_flood_risk": len(property_ids & flood_property_ids),
            "loans_with_flood_risk": len(loan_ids & flood_loan_ids),
        },
    }
