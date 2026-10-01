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

"""Small platform records for one commercial asset, and ready-made cases.

Three events: EVT-A is a two-storm event, EVT-B and EVT-C one storm each. The
asset floods in EVT-A only; the reference gauge passes Severe in EVT-A and EVT-C,
so EVT-C is a payout with no flood at the asset -- basis risk in both directions
is present.
"""

import numpy as np

from models.capital.asset_inputs import AssetCase

ASSET_ID = "CPROP-test0001"


def _storm(storm_id, category="severe"):
    return {"storm_id": storm_id, "precipitation_mm": 50.0, "duration_hours": 24,
            "intensity_factor": 1.5, "intensity_category": category, "peak_position": 0.5}


SEQUENCES = {"sequences": [
    {"sequence_id": "EVT-A", "storms": [_storm("S-A1"), _storm("S-A2", "extreme")]},
    {"sequence_id": "EVT-B", "storms": [_storm("S-B1", "moderate")]},
    {"sequence_id": "EVT-C", "storms": [_storm("S-C1")]},
]}

ASSET = {"CommercialAsset": {
    "Header": {"PropertyID": ASSET_ID},
    "Valuation": {"PropertyValue": 10_000_000.0},
    "Tenancy": {"NetInitialYield": 0.06},
}}

LOAN = {"Mortgage": {
    "Header": {"MortgageID": "CLOAN-test0001", "PropertyID": ASSET_ID},
    "CurrentStatus": {"OutstandingBalance": 6_000_000.0, "CurrentInterestRate": 0.05,
                      "RemainingTerm": 60},
    "Features": {"RepaymentType": "Interest only"},
}}

TIMESERIES = {
    "property_id": ASSET_ID,
    "nearest_gauges": [
        {"gauge_id": "SYNTH-0001", "distance_m": 900.0},
        {"gauge_id": "GAUGE-0002", "distance_m": 4000.0},
        {"gauge_id": "GAUGE-0003", "distance_m": 9000.0},
    ],
    # The flood series names its field storm_id but stores event ids.
    "flood_events": [
        {"storm_id": "EVT-A", "flood_depth_m": 0.8, "damage_ratio": 0.35},
        {"storm_id": "EVT-B", "flood_depth_m": 0.0, "damage_ratio": 0.0},
    ],
}

REFERENCE_RESPONSES = [
    {"storm_id": "S-A2", "exceeded_severe": True},
    {"storm_id": "S-A1", "exceeded_severe": False},
    {"storm_id": "S-B1", "exceeded_severe": False},
    {"storm_id": "S-C1", "exceeded_severe": True},
]


def make_case(damage, triggered, *, weights=None, lam=2.0, coverage=1.0,
              rent_yield=0.06, balance=6_000_000.0, rate=0.05, amortising=0.0):
    """An ``AssetCase`` with chosen per-event damage and triggers."""
    damage = np.asarray(damage, dtype=float)
    n = damage.size
    weights = np.full(n, 1.0 / n) if weights is None else np.asarray(weights, dtype=float)
    return AssetCase(
        asset_id=ASSET_ID, catchment="thames",
        event_ids=tuple(f"EVT-{i}" for i in range(n)),
        event_weights=weights, event_coverage=coverage, lambda_per_year=lam,
        damage_ratio=damage, flood_depth_m=damage * 2.0,
        triggered=np.asarray(triggered, dtype=bool),
        reference_gauge_id="GAUGE-0002", controlling_gauge_id="SYNTH-0001",
        property_value=10_000_000.0, net_initial_yield=rent_yield,
        loan_balance=balance, interest_rate=rate, remaining_term_years=5.0,
        amortising_share=amortising,
    )
