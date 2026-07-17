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

"""Promoted-column extraction for the relational shred (JSON→Postgres WP1.6).

For each artifact, maps a table column → the path to its value inside a record.
Used by ``pg_repo`` on save to populate the typed, indexed columns alongside the
verbatim ``cdm`` — that's what makes the relational queries work. Extraction is
tolerant: a missing path yields ``None`` (records vary), and ``cdm`` is always
the source of truth, so a gap here never costs data.
"""

from typing import Any

# artifact -> {column: path-within-a-record}. Single-element paths address a
# flat record (the dict-container hazard curve, the flat eod snapshot).
_PROMOTED: dict[str, dict[str, tuple]] = {
    "gauge": {
        "gauge_name": ("FloodGauge", "Header", "GaugeName"),
        "latitude": ("FloodGauge", "Location", "GaugeLatitude"),
        "longitude": ("FloodGauge", "Location", "GaugeLongitude"),
        "elevation": ("FloodGauge", "Location", "GaugeElevation"),
        "flood_alert": ("FloodGauge", "FloodStages", "FloodAlert"),
        "flood_warning": ("FloodGauge", "FloodStages", "FloodWarning"),
        "severe_flood_warning": ("FloodGauge", "FloodStages", "SevereFloodWarning"),
        "nrfa_station_id": ("FloodGauge", "NRFAMetadata", "NRFAStationID"),
    },
    "property": {
        "uprn": ("PropertyHeader", "Header", "UPRN"),
        "property_type": ("PropertyHeader", "Header", "propertyType"),
        "status": ("PropertyHeader", "Header", "propertyStatus"),
        "property_value": ("PropertyHeader", "Valuation", "PropertyValue"),
        "latitude": ("PropertyHeader", "Location", "LatitudeDegrees"),
        "longitude": ("PropertyHeader", "Location", "LongitudeDegrees"),
        "postcode": ("PropertyHeader", "Location", "Postcode"),
        "town_city": ("PropertyHeader", "Location", "TownCity"),
        "local_authority": ("PropertyHeader", "Location", "LocalAuthority"),
        "area_sqm": ("PropertyHeader", "PropertyAttributes", "PropertyAreaSqm"),
        "construction_year": ("PropertyHeader", "PropertyAttributes", "ConstructionYear"),
        "ea_flood_zone": ("PropertyHeader", "RiskAssessment", "EAFloodZone"),
        "overall_flood_risk": ("PropertyHeader", "RiskAssessment", "OverallFloodRisk"),
    },
    "loan": {
        "property_id": ("RLoan", "Header", "PropertyID"),
        "uprn": ("RLoan", "Header", "UPRN"),
        "currency": ("RLoan", "FinancialTerms", "currency"),
        "original_loan": ("RLoan", "FinancialTerms", "OriginalLoan"),
        "original_ltv": ("RLoan", "FinancialTerms", "OriginalLTV"),
        "outstanding_balance": ("RLoan", "CurrentStatus", "OutstandingBalance"),
        "current_ltv": ("RLoan", "CurrentStatus", "CurrentLTV"),
        "account_status": ("RLoan", "CurrentStatus", "AccountStatus"),
        "default_flag": ("RLoan", "CurrentStatus", "DefaultFlag"),
        "arrears_months": ("RLoan", "CurrentStatus", "ArrearsMonths"),
    },
    "commercial": {
        "uprn": ("CommercialAsset", "Header", "UPRN"),
        "property_type": ("CommercialAsset", "Header", "propertyType"),
        "status": ("CommercialAsset", "Header", "propertyStatus"),
        "property_value": ("CommercialAsset", "Valuation", "PropertyValue"),
    },
    "commercial_loan": {
        "property_id": ("Mortgage", "Header", "PropertyID"),
        "uprn": ("Mortgage", "Header", "UPRN"),
        "borrower_type": ("_commercial_meta", "borrower_type"),
        "commercial_type": ("_commercial_meta", "commercial_type"),
    },
    "counterparty": {
        "party_name": ("CounterpartySet", "Party", "PartyName"),
        "party_id_scheme": ("CounterpartySet", "Party", "PartyIdScheme"),
    },
    "gauge_hazard_curve": {
        "gauge_name": ("gauge_name",),
        "latitude": ("latitude",),
        "longitude": ("longitude",),
        "gev_location": ("gev_location",),
        "gev_scale": ("gev_scale",),
        "gev_shape": ("gev_shape",),
        "annual_hazard_rate_alert": ("annual_hazard_rate_alert",),
        "annual_hazard_rate_warning": ("annual_hazard_rate_warning",),
        "annual_hazard_rate_severe": ("annual_hazard_rate_severe",),
    },
    "prs_trade": {
        "trade_type": ("PhysicalSwap", "Header", "TradeType"),
        "counterparty": ("PhysicalSwap", "Header", "CounterParty"),
        "party_id": ("PhysicalSwap", "Header", "PartyId"),
        "trade_status": ("PhysicalSwap", "Header", "TradeStatus"),
        "valuation_date": ("PhysicalSwap", "Header", "ValuationDate"),
        "notional": ("PhysicalSwap", "LegData", "Notional"),
        "currency": ("PhysicalSwap", "LegData", "Currency"),
        "spread_bps": ("PhysicalSwap", "Pricing", "SpreadBps"),
        "npv": ("PhysicalSwap", "Pricing", "NPV"),
        "trigger_level": ("PhysicalSwap", "Pricing", "TriggerLevel"),
    },
    "eod_snapshot": {
        "eod_id": ("eod_id",),
        "generated_at": ("generated_at",),
        "num_open_trades": ("portfolio_summary", "num_open_trades"),
        "total_notional": ("portfolio_summary", "total_notional"),
        "total_daily_pnl": ("portfolio_summary", "total_daily_pnl"),
        "total_running_pnl": ("portfolio_summary", "total_running_pnl"),
    },
}


def _get(record: Any, path: tuple) -> Any:
    cur = record
    for part in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def promoted_columns(artifact: str, record: dict) -> dict:
    """Return ``{column: value}`` for ``artifact``'s promoted columns, reading
    each from its path in ``record`` (missing → ``None``)."""
    return {col: _get(record, path) for col, path in _PROMOTED.get(artifact, {}).items()}
