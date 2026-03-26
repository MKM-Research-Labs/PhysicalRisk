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


def extract_mortgage_ids(mortgage_data: Optional[Dict[str, Any]]) -> Set[str]:
    """Extract all mortgage IDs from mortgage data."""
    if not mortgage_data:
        return set()

    ids = set()
    for mortgage in mortgage_data.get("items", []):
        mort_id = mortgage.get("Mortgage", {}).get("Header", {}).get("MortgageID")
        if mort_id:
            ids.add(mort_id)
    return ids


def extract_mortgage_property_ids(mortgage_data: Optional[Dict[str, Any]]) -> Set[str]:
    """Extract property IDs referenced in mortgage data."""
    if not mortgage_data:
        return set()

    ids = set()
    for mortgage in mortgage_data.get("items", []):
        prop_id = mortgage.get("Mortgage", {}).get("Header", {}).get("PropertyID")
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
    mortgage_data: Optional[Dict[str, Any]] = None,
    flood_risk_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze relationships between IDs in different datasets.

    Returns:
        Dictionary with ID counts and overlap statistics
    """
    property_ids = extract_property_ids(property_data)
    mortgage_property_ids = extract_mortgage_property_ids(mortgage_data)
    mortgage_ids = extract_mortgage_ids(mortgage_data)

    # Extract IDs from flood risk data (gaugehc.json has hazard_curves key)
    flood_property_ids = set()
    if flood_risk_data:
        # Property IDs from property hazard curves
        flood_property_ids = set(flood_risk_data.get("property_hazard_curves", {}).keys())
        # Also check legacy format
        if not flood_property_ids:
            flood_property_ids = set(flood_risk_data.get("property_risk", {}).keys())

    # Mortgages with flood risk = mortgages whose property has flood risk
    flood_mortgage_ids = set()
    if mortgage_data and flood_property_ids:
        for mortgage in mortgage_data.get("items", []):
            mort = mortgage.get("Mortgage", {}).get("Header", {})
            prop_id = mort.get("PropertyID")
            mort_id = mort.get("MortgageID")
            if prop_id in flood_property_ids and mort_id:
                flood_mortgage_ids.add(mort_id)

    return {
        "counts": {
            "properties": len(property_ids),
            "mortgages": len(mortgage_ids),
            "mortgage_properties": len(mortgage_property_ids),
            "flood_properties": len(flood_property_ids),
            "flood_mortgages": len(flood_mortgage_ids),
        },
        "overlaps": {
            "properties_with_mortgages": len(property_ids & mortgage_property_ids),
            "properties_with_flood_risk": len(property_ids & flood_property_ids),
            "mortgages_with_flood_risk": len(mortgage_ids & flood_mortgage_ids),
        },
    }
