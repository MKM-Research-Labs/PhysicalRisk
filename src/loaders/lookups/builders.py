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

"""
Lookup table builders linking properties, mortgages, gauges, and flood risk data.
"""

from typing import Any, Dict, Optional


def build_rloan_lookup(rloan_data: Optional[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Build property_id -> mortgage mapping.

    Args:
        rloan_data: Raw mortgage data with 'items' key

    Returns:
        Dictionary mapping property IDs to mortgage information
    """
    if not rloan_data:
        return {}

    lookup = {}
    mortgages = rloan_data.get("items", [])

    for mortgage in mortgages:
        mort_data = mortgage.get("RLoan", {})
        header = mort_data.get("Header", {})
        property_id = header.get("PropertyID")

        if property_id:
            financial_terms = mort_data.get("FinancialTerms", {})
            current_status = mort_data.get("CurrentStatus", {})

            lookup[property_id] = {
                "mortgage_id": header.get("RLoanID"),
                "property_id": property_id,
                "uprn": header.get("UPRN"),
                "financial_terms": financial_terms,
                "application": mort_data.get("Application", {}),
                # Flatten key financial fields for direct access
                "OriginalLoan": financial_terms.get("OriginalLoan", 0),
                "OriginalLTV": financial_terms.get("OriginalLTV", 0),
                "OriginalLendingRate": financial_terms.get("OriginalLendingRate", 0),
                "OriginalTerm": financial_terms.get("OriginalTerm", 0),
                "CurrentBalance": current_status.get("OutstandingBalance", 0),
                "CurrentLTV": current_status.get("CurrentLTV", 0),
                "CurrentInterestRate": current_status.get("CurrentInterestRate", 0),
            }

    return lookup


def build_gauge_flood_info(
    gauge_data: Optional[Dict[str, Any]],
    flood_risk_data: Optional[Dict[str, Any]]
) -> Dict[str, Dict]:
    """
    Build gauge_id -> flood info mapping from hazard curve data and gauge data.

    Args:
        gauge_data: Raw gauge data with 'items' key containing FloodGauge records
        flood_risk_data: Hazard curve data with 'hazard_curves' key (from gaugehc.json)

    Returns:
        Dictionary mapping gauge IDs to flood information
    """
    lookup = {}

    # Extract from hazard curves (gaugehc.json) — primary source
    if flood_risk_data:
        hazard_curves = flood_risk_data.get("hazard_curves", {})
        for gauge_id, hc in hazard_curves.items():
            lookup[gauge_id] = {
                "gauge_name": hc.get("gauge_name"),
                "elevation": hc.get("elevation_m"),
                "alert_level": hc.get("flood_alert_m"),
                "warning_level": hc.get("flood_warning_m"),
                "severe_level": hc.get("severe_flood_warning_m"),
                "annual_flood_prob_alert": hc.get("annual_flood_prob_alert"),
                "annual_flood_prob_warning": hc.get("annual_flood_prob_warning"),
                "annual_flood_prob_severe": hc.get("annual_flood_prob_severe"),
                "hazard_rate_alert": hc.get("annual_hazard_rate_alert"),
                "hazard_rate_warning": hc.get("annual_hazard_rate_warning"),
                "hazard_rate_severe": hc.get("annual_hazard_rate_severe"),
            }

    # Supplement with gauge data (gauge.json) if available
    if gauge_data:
        for gauge in gauge_data.get("items", []):
            fg = gauge.get("FloodGauge", {})
            header = fg.get("Header", {})
            gauge_id = header.get("GaugeID")
            if not gauge_id:
                continue

            flood_stages = fg.get("FloodStages", {})
            location = fg.get("Location", {})
            sensor_stats = fg.get("SensorStats", {})

            if gauge_id not in lookup:
                lookup[gauge_id] = {}

            # Fill in fields not already set from hazard data
            existing = lookup[gauge_id]
            existing.setdefault("gauge_name", header.get("GaugeName"))
            existing.setdefault("elevation", location.get("GaugeElevation"))
            existing.setdefault("alert_level", flood_stages.get("FloodAlert"))
            existing.setdefault("warning_level", flood_stages.get("FloodWarning"))
            existing.setdefault("severe_level", flood_stages.get("SevereFloodWarning"))
            existing.setdefault("max_level", sensor_stats.get("HistoricalHighLevel"))
            existing.setdefault("max_gauge_reading", sensor_stats.get("HistoricalHighLevel"))

    return lookup


def build_property_flood_info(
    property_data: Optional[Dict[str, Any]],
    flood_risk_data: Optional[Dict[str, Any]],
    property_hazard_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict]:
    """
    Build property_id -> flood info mapping from property hazard curves.

    Args:
        property_data: Raw property data with 'items' key
        flood_risk_data: Gauge hazard data (used for gauge-level context)
        property_hazard_data: Property hazard curve data from propertyhc.json

    Returns:
        Dictionary mapping property IDs to flood risk information
    """
    lookup = {}

    # Extract from property hazard curves (propertyhc.json) — primary source
    if property_hazard_data:
        phc = property_hazard_data.get("property_hazard_curves", {})
        for prop_id, prop_hc in phc.items():
            location = prop_hc.get("location", {})
            depth_thresholds = prop_hc.get("depth_thresholds", {})
            any_flood = depth_thresholds.get("any_flood", {})
            moderate = depth_thresholds.get("moderate", {})
            severe = depth_thresholds.get("severe", {})

            lookup[prop_id] = {
                "property_id": prop_id,
                "property_elevation": prop_hc.get("elevation_m"),
                "floor_level": prop_hc.get("floor_level_m"),
                "flood_count": prop_hc.get("flood_count", 0),
                "annual_flood_prob": any_flood.get("annual_probability", 0),
                "return_period_years": any_flood.get("return_period_yrs"),
                "moderate_flood_prob": moderate.get("annual_probability", 0),
                "severe_flood_prob": severe.get("annual_probability", 0),
                "risk_level": _classify_property_risk(any_flood.get("annual_probability", 0)),
                "lat": location.get("lat"),
                "lon": location.get("lon"),
            }

    # Supplement with property data (property.json) for properties not in hazard data
    if property_data:
        for prop in property_data.get("items", []):
            ph = prop.get("PropertyHeader", {})
            header = ph.get("Header", {})
            prop_id = header.get("PropertyID")
            if not prop_id or prop_id in lookup:
                continue

            risk_assessment = ph.get("RiskAssessment", {})
            location = ph.get("Location", {})

            lookup[prop_id] = {
                "property_id": prop_id,
                "property_elevation": risk_assessment.get("GroundLevelMeters"),
                "flood_zone": risk_assessment.get("EAFloodZone"),
                "overall_risk": risk_assessment.get("OverallFloodRisk"),
                "risk_level": risk_assessment.get("OverallFloodRisk", "Unknown"),
                "lat": location.get("LatitudeDegrees"),
                "lon": location.get("LongitudeDegrees"),
            }

    return lookup


def _classify_property_risk(annual_prob: float) -> str:
    """Classify property flood risk based on annual probability."""
    if annual_prob >= 0.03:
        return "High"
    elif annual_prob >= 0.01:
        return "Medium"
    elif annual_prob > 0:
        return "Low"
    return "Negligible"


def build_all_lookups(
    gauge_data: Optional[Dict[str, Any]] = None,
    property_data: Optional[Dict[str, Any]] = None,
    rloan_data: Optional[Dict[str, Any]] = None,
    flood_risk_data: Optional[Dict[str, Any]] = None,
    property_hazard_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict]:
    """
    Build all cross-reference lookups in one call.

    Args:
        gauge_data: Raw gauge data
        property_data: Raw property data
        rloan_data: Raw mortgage data
        flood_risk_data: Gauge hazard curve data (from gaugehc.json)
        property_hazard_data: Property hazard curve data (from propertyhc.json)

    Returns:
        Dictionary containing all lookup tables
    """
    property_flood_info = build_property_flood_info(
        property_data, flood_risk_data, property_hazard_data
    )

    return {
        "rloan_lookup": build_rloan_lookup(rloan_data),
        "gauge_flood_info": build_gauge_flood_info(gauge_data, flood_risk_data),
        "property_flood_info": property_flood_info,
    }
