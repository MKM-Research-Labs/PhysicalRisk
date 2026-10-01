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

"""Everything the capital model needs about one real commercial asset.

Built from what the platform already computes, rather than re-derived:

- The **event catalogue**: storms grouped into hours-clause events, each with a
  sampling weight, and the catchment's annual event rate (MKM-EF-001).
- The asset's **flood depth per event**, from its commercial flood series. The
  platform computes it from the controlling (synthetic) gauge, the asset's
  ground and floor levels, its distance and terrain.
- Whether the PRS **reference gauge** -- the asset's nearest real gauge, which is
  what the property PRS book trades on -- passed Severe Flood Warning in the
  event. Depth and trigger come from different gauges; the gap is basis risk.
- The **investor and loan**: value, net initial yield, balance, rate, term.

``build_asset_case`` takes plain records so it can be tested without a
database; ``load_asset_case`` reads them through ``database``.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

import database
from config.capital import AMORTISING_SHARE, ASSET_TIMESERIES_MODE, SYNTHETIC_GAUGE_PREFIX
from config.frequency import catchment_lambda
from models.frequency import build_event_frame
from models.hazard.io import load_storms_from_sequences

MONTHS_PER_YEAR = 12


@dataclass(frozen=True)
class AssetCase:
    """One asset's hazard, trigger and finances, on the platform's event catalogue.

    Event arrays are aligned with ``event_ids`` (the catalogue's order).
    """
    asset_id: str
    catchment: str
    event_ids: tuple
    event_weights: np.ndarray        # sampling weights, summing to one
    event_coverage: float            # share of all events the catalogue represents
    lambda_per_year: float           # catchment event arrival rate
    damage_ratio: np.ndarray         # platform damage ratio at the asset, per event
    flood_depth_m: np.ndarray        # flood depth above floor at the asset, per event
    triggered: np.ndarray            # reference gauge passed Severe, per event
    reference_gauge_id: str
    controlling_gauge_id: str
    property_value: float
    net_initial_yield: float
    loan_balance: float
    interest_rate: float
    remaining_term_years: float
    amortising_share: float

    @property
    def annual_rent(self) -> float:
        """Passing rent: net initial yield on market value."""
        return self.net_initial_yield * self.property_value

    @property
    def annual_debt_service(self) -> float:
        """Interest plus the amortising share of the balance over the remaining term."""
        amortisation = (self.amortising_share * self.loan_balance
                        / max(self.remaining_term_years, 1.0))
        return self.loan_balance * self.interest_rate + amortisation


def build_asset_case(asset: Dict, loan: Dict, timeseries: Dict, sequences: Dict,
                     reference_responses: List[Dict], lambda_per_year: float,
                     catchment: str) -> AssetCase:
    """Assemble an ``AssetCase`` from the platform's records for one asset."""
    ca = asset.get("CommercialAsset", asset)
    mortgage = loan.get("Mortgage", loan)
    frame = build_event_frame(load_storms_from_sequences(sequences))
    position = {event: i for i, event in enumerate(frame.event_ids)}

    depth = np.zeros(frame.n_events)
    damage = np.zeros(frame.n_events)
    for event in timeseries.get("flood_events", []):
        i = _event_index(event.get("storm_id", ""), position, frame.event_of)
        if i is not None:
            depth[i] = max(depth[i], float(event.get("flood_depth_m", 0.0)))
            damage[i] = max(damage[i], float(event.get("damage_ratio", 0.0)))

    triggered = np.zeros(frame.n_events, dtype=bool)
    for response in reference_responses:
        if response.get("exceeded_severe"):
            i = _event_index(response.get("storm_id", ""), position, frame.event_of)
            if i is not None:
                triggered[i] = True

    nearest = timeseries.get("nearest_gauges", [])
    status = mortgage.get("CurrentStatus", {})
    return AssetCase(
        asset_id=ca["Header"]["PropertyID"],
        catchment=catchment,
        event_ids=frame.event_ids,
        event_weights=np.asarray(frame.weights, dtype=float),
        event_coverage=float(frame.coverage),
        lambda_per_year=float(lambda_per_year),
        damage_ratio=damage,
        flood_depth_m=depth,
        triggered=triggered,
        reference_gauge_id=reference_gauge(nearest),
        controlling_gauge_id=nearest[0]["gauge_id"] if nearest else "",
        property_value=float(ca["Valuation"]["PropertyValue"]),
        net_initial_yield=float(ca["Tenancy"]["NetInitialYield"]),
        loan_balance=float(status["OutstandingBalance"]),
        interest_rate=float(status["CurrentInterestRate"]),
        remaining_term_years=float(status["RemainingTerm"]) / MONTHS_PER_YEAR,
        amortising_share=AMORTISING_SHARE.get(
            mortgage.get("Features", {}).get("RepaymentType", ""), 0.0),
    )


def reference_gauge(nearest: List[Dict]) -> str:
    """The PRS reference gauge: the nearest real gauge, as the property book uses."""
    for gauge in nearest:
        if not gauge["gauge_id"].startswith(SYNTHETIC_GAUGE_PREFIX):
            return gauge["gauge_id"]
    raise ValueError("asset has no real gauge among its nearest gauges")


def load_asset_case(catchment: str, asset_id: str) -> AssetCase:
    """Read one commercial asset's records through ``database`` and build its case.

    The asset and loan are found by scanning the lists: ``get_commercial`` and
    ``get_commercial_loan`` match only top-level ids and cannot see the nested
    ``CommercialAsset.Header.PropertyID`` real records carry.
    """
    asset = _find(database.list_commercial(catchment),
                  lambda r: r.get("CommercialAsset", {}).get("Header", {}).get("PropertyID"),
                  asset_id, "commercial asset")
    loan = _find(database.list_commercial_loans(catchment),
                 lambda r: r.get("Mortgage", {}).get("Header", {}).get("PropertyID"),
                 asset_id, "commercial loan for")
    timeseries = database.get_commercial_timeseries(catchment, asset_id, ASSET_TIMESERIES_MODE)
    if not timeseries:
        raise ValueError(f"no flood series for {asset_id}")
    ref = reference_gauge(timeseries.get("nearest_gauges", []))
    gaugets = database.get_gauge_timeseries(catchment, ref) or {}
    responses = gaugets.get("storm_responses", {}).get("responses", [])
    return build_asset_case(asset, loan, timeseries,
                            database.get_storm_sequences(catchment) or {},
                            responses, catchment_lambda(catchment), catchment)


def _event_index(identifier: str, position: Dict[str, int],
                 event_of: Dict[str, str]) -> Optional[int]:
    """Index of the event a storm or event id belongs to, or None if unknown."""
    if identifier in position:
        return position[identifier]
    event = event_of.get(identifier)
    return position.get(event) if event is not None else None


def _find(records, key, wanted, what):
    for record in records:
        if key(record) == wanted:
            return record
    raise ValueError(f"no {what} {wanted}")
