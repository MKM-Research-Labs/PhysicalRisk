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
Data structures for hazard curve computation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GaugeResponse:
    """Response of a single gauge to a storm."""
    gauge_id: str
    storm_id: str
    base_level_m: float
    level_change_m: float
    peak_level_m: float
    exceeded_alert: bool
    exceeded_warning: bool
    exceeded_severe: bool


@dataclass
class HazardCurvePoint:
    """A single point on the hazard curve."""
    threshold_m: float
    annual_exceedance_prob: float
    return_period_years: float


@dataclass
class TermStructurePoint:
    """A single point on the term structure for PRS pricing."""
    year: int
    expected_floods: float
    prob_at_least_one: float
    survival_prob: float
    cumulative_default_prob: float


@dataclass
class GaugeHazardCurve:
    """Complete hazard curve for a single gauge."""
    gauge_id: str
    gauge_name: str
    latitude: float
    longitude: float
    elevation_m: float

    # Flood thresholds
    flood_alert_m: float
    flood_warning_m: float
    severe_flood_warning_m: float

    # GEV parameters
    gev_location: float
    gev_scale: float
    gev_shape: float

    # Hazard curve points
    curve_points: List[HazardCurvePoint]
    return_period_levels: Dict[str, float]

    # Annual flood probabilities
    annual_flood_prob_alert: float
    annual_flood_prob_warning: float
    annual_flood_prob_severe: float

    # Term structure for PRS pricing
    annual_hazard_rate_alert: float
    annual_hazard_rate_warning: float
    annual_hazard_rate_severe: float
    term_structure_alert: List[TermStructurePoint]
    term_structure_warning: List[TermStructurePoint]
    term_structure_severe: List[TermStructurePoint]

    # Metadata
    num_storms_simulated: int
    simulation_timestamp: str

    # Event frequency layer (MKM-EF-001). Optional so that a curve built
    # without the frequency layer still constructs; when present, the annual
    # probabilities above are derived from these rather than being a per-event
    # conditional relabelled as annual.
    num_events_simulated: int = 0
    lambda_per_year: float = 0.0
    event_exceedance_prob_alert: float = 0.0
    event_exceedance_prob_warning: float = 0.0
    event_exceedance_prob_severe: float = 0.0
    implied_return_period_severe_years: float = 0.0
    # Raw count of catalogue events exceeding the severe level at this gauge.
    # Unweighted and unannualised on purpose: the basis leg compares it with a
    # property's raw flood-event count, and the two must share a basis.
    severe_event_count: int = 0
    # The pre-frequency metric, retained for parallel-run comparison until the
    # switchover is signed off.
    legacy_annual_flood_prob_severe: float = 0.0
    # Loss-weighted view (MKM-EF-001 Stage 6c, additive). A compact summary of
    # the event loss table and annual loss distribution — average annual loss,
    # AEP/OEP curves and the reconciliation verdict — at unit exposure, since a
    # gauge carries no asset value. None when the curve is built without the
    # loss layer. Does not feed the spread; it is an additional output.
    loss_metrics: Optional[Dict] = None
