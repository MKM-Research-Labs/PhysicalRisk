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
Analytical PRS (Physical Risk Swap) pricing without QuantLib dependency.

Implements quarterly CDS-equivalent pricing per PRS Property Pricing Spec Section 6.1,
plus the 5-component basis waterfall per Spec Section 4.

Functions:
    compute_prs_spread: Fair spread from hazard rate, tenor, recovery
    compute_basis_waterfall: Distance/elevation/terrain/composition basis
"""

import math
from typing import Dict, List, Optional

from config.models import (
    COMPOSITION_BASIS_BPS,
    CONSTRUCTION_YEAR_CUTOFF,
    DISTANCE_CAP_KM,
    DISTANCE_MAX_BPS,
    DISTANCE_RATE_BPS_PER_KM,
    ELEVATION_MAX_BENEFIT_BPS,
    ELEVATION_RATE_BPS_PER_M,
    MIN_PRS_SPREAD_BPS,
    MODEL_UNCERTAINTY_BPS,
    RECOVERY_RATES,
    TERRAIN_BASIS_BPS,
)


def interpolate_yield_rate(yield_curve: dict, t: float,
                           fallback: float = 0.04) -> float:
    """
    Interpolate yield rate at time t (years) from curve points.

    Args:
        yield_curve: Dict mapping tenor (str keys like '1','2') to rate
        t: Time in years (can be fractional, e.g. 0.25)
        fallback: Rate to use if curve is empty

    Returns:
        Interpolated continuous yield rate
    """
    if not yield_curve:
        return fallback
    keys = sorted(int(k) for k in yield_curve.keys())
    if not keys:
        return fallback
    if t <= keys[0]:
        return yield_curve[str(keys[0])]
    if t >= keys[-1]:
        return yield_curve[str(keys[-1])]
    for i in range(len(keys) - 1):
        if keys[i] <= t <= keys[i + 1]:
            t0, t1 = keys[i], keys[i + 1]
            r0, r1 = yield_curve[str(t0)], yield_curve[str(t1)]
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return yield_curve[str(keys[-1])]


def compute_prs_spread(
    annual_hazard_rate: float,
    tenor: int,
    recovery: float = 0.0,
    risk_free_rate: float = 0.03,
    min_spread_bps: float = MIN_PRS_SPREAD_BPS,
    yield_curve: Optional[dict] = None,
) -> float:
    """
    Compute PRS fair spread in basis points using quarterly CDS-equivalent pricing.

    Implements Spec Section 6.1:
        - Converts annual probability to continuous hazard rate (Eq. 7)
        - Computes risky annuity: sum of dt * S(t) * DF(t)
        - Computes protection leg PV: (1-R) * sum of (S(t-1) - S(t)) * DF(t)
        - Fair spread = protection_pv / annuity

    Args:
        annual_hazard_rate: Annual default/flood probability (0-1)
        tenor: Maturity in years
        recovery: Recovery rate (0-1), trigger-dependent per Spec Table 5
        risk_free_rate: Risk-free discount rate (continuous)
        min_spread_bps: Floor spread in basis points

    Returns:
        Fair spread in basis points
    """
    if annual_hazard_rate <= 0:
        return 0.0

    # Convert annual probability to continuous hazard rate (Spec Eq. 7)
    hazard_lambda = -math.log(1.0 - min(annual_hazard_rate, 0.999))

    dt = 0.25  # Quarterly periods (Spec Section 6.1)
    n_periods = tenor * 4

    # Risky annuity: sum of dt * S(t) * DF(t)
    annuity = 0.0
    for i in range(1, n_periods + 1):
        t = i * dt
        survival = math.exp(-hazard_lambda * t)
        rf = interpolate_yield_rate(yield_curve, t, risk_free_rate) if yield_curve else risk_free_rate
        discount = math.exp(-rf * t)
        annuity += dt * survival * discount

    if annuity <= 0:
        return annual_hazard_rate * 10000  # Fallback

    # Protection leg PV: (1-R) * sum of (S(t-1) - S(t)) * DF(t)
    protection_pv = 0.0
    for i in range(1, n_periods + 1):
        t = i * dt
        t_prev = (i - 1) * dt
        surv_prev = math.exp(-hazard_lambda * t_prev)
        surv_curr = math.exp(-hazard_lambda * t)
        default_prob = surv_prev - surv_curr
        t_mid = t - dt / 2
        rf = interpolate_yield_rate(yield_curve, t_mid, risk_free_rate) if yield_curve else risk_free_rate
        discount = math.exp(-rf * t_mid)
        protection_pv += (1.0 - recovery) * default_prob * discount

    fair_spread = protection_pv / annuity if annuity > 0 else 0.0
    spread_bps = fair_spread * 10000  # Convert to bps
    return max(spread_bps, min_spread_bps)


def compute_basis_waterfall(
    prop_elevation: float,
    flood_zone: str,
    property_type: str,
    construction_year: int,
    nearest_gauges: List[Dict],
) -> Dict:
    """
    Compute 5-component basis waterfall per PRS Property Pricing Spec Section 4.

    Components:
        1. Model uncertainty (+2bp fixed)
        2. Distance basis (0.5bp/km, capped at 6bp)
        3. Elevation basis (-0.2bp/m above gauge, capped at -3bp)
        4. Terrain variation (by EA flood zone)
        5. Property composition (by type + construction year)

    Args:
        prop_elevation: Property ground elevation in meters
        flood_zone: EA flood zone classification
        property_type: Property type (Detached, Semi-detached, etc.)
        construction_year: Year of construction
        nearest_gauges: List of dicts with 'distance_m' and 'gauge_elevation_m'

    Returns:
        Dictionary with each basis component and total
    """
    # 1. Model uncertainty (fixed)
    basis_model = MODEL_UNCERTAINTY_BPS

    # 2. Distance basis
    distances_km = [ng.get('distance_m', 0) / 1000 for ng in nearest_gauges]
    if not distances_km:
        distances_km = [1.0]
    weights = [1.0 / max(d, 0.1) for d in distances_km]
    w_total = sum(weights)
    weights = [w / w_total for w in weights]
    d_weighted = sum(d * w for d, w in zip(distances_km, weights))
    d_weighted = min(d_weighted, DISTANCE_CAP_KM)
    basis_distance = min(DISTANCE_MAX_BPS, DISTANCE_RATE_BPS_PER_KM * d_weighted)

    # 3. Elevation basis
    gauge_elevs = [ng.get('gauge_elevation_m', 0) for ng in nearest_gauges]
    if not gauge_elevs:
        gauge_elevs = [prop_elevation]
    weighted_gauge_elev = sum(e * w for e, w in zip(gauge_elevs, weights))
    elev_diff = prop_elevation - weighted_gauge_elev
    if elev_diff > 0:
        basis_elevation = max(-ELEVATION_MAX_BENEFIT_BPS,
                              -ELEVATION_RATE_BPS_PER_M * elev_diff)
    else:
        basis_elevation = 0.0

    # 4. Terrain variation
    basis_terrain = TERRAIN_BASIS_BPS.get(flood_zone, 0.0)

    # 5. Property composition
    basis_composition = COMPOSITION_BASIS_BPS.get(property_type, 0.0)
    if construction_year < CONSTRUCTION_YEAR_CUTOFF:
        basis_composition += 1.0

    total_basis = (basis_model + basis_distance + basis_elevation
                   + basis_terrain + basis_composition)

    return {
        'model_uncertainty_bp': round(basis_model, 1),
        'distance_bp': round(basis_distance, 1),
        'elevation_bp': round(basis_elevation, 1),
        'terrain_bp': round(basis_terrain, 1),
        'composition_bp': round(basis_composition, 1),
        'total_basis_bp': round(total_basis, 1),
        'weighted_distance_km': round(d_weighted, 2),
        'elevation_diff_m': round(elev_diff, 2),
        'flood_zone': flood_zone,
        'property_type': property_type,
        'construction_year': construction_year,
    }
