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
Data structures for hazard curve computation.
"""

from dataclasses import dataclass
from typing import Dict, List


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
