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
One-step state propagator for the typhoon model.

Implements the four transition blocks from the Bayesian typhoon progression
specification:

1. Motion update (spec eq. 5) — regime-conditioned Gaussian on speed and heading
2. Position update (spec eqs. 6-7) — Haversine forward by (u_t * dt, psi_t)
3. Intensity update (spec eqs. 8-9) — over-water drift, over-land exponential decay
4. Size update (spec eq. 10) — log-space mean-reverting around V-conditional target

The model is catchment-agnostic: the catchment supplies parameter dataclasses
and a land_mask via CatchmentTyphoonConfig. The transition layer enforces
physical invariants (R_max < R_outer, V_max >= 0, lat in [-90, 90]).

Conventions:
- Heading in compass degrees: 0 = North, increasing clockwise.
- Position in WGS-84-style longitude/latitude, degrees.
- Equirectangular advection: adequate for tropical/sub-tropical hourly steps.
"""

import math
from typing import List, Tuple

import numpy as np

from config.typhoon import (
    CatchmentTyphoonConfig,
    IntensityParams,
    MotionParams,
    SizeParams,
)
from models.typhoon.data_structures import RegimeClass, TyphoonState


__all__ = [
    "wrap_compass_degrees",
    "signed_compass_delta",
    "haversine_step",
    "update_motion",
    "update_position",
    "update_wind",
    "update_size",
    "step",
    "advance",
    "EARTH_RADIUS_KM",
    "RECURVATURE_REGIMES",
]


# Mean Earth radius used by the equirectangular advection step.
EARTH_RADIUS_KM: float = 6371.0

# Regimes that apply a northward recurvature bias when above the
# recurvature latitude. SHARP_RECURVE is included because by definition
# it implies a steeper northward turn at the recurvature latitude.
RECURVATURE_REGIMES = frozenset({RegimeClass.NW_RECURVER, RegimeClass.SHARP_RECURVE})


# ===========================================================================
# Compass-degree helpers (circular arithmetic)
# ===========================================================================


def wrap_compass_degrees(deg: float) -> float:
    """Wrap an angle to the compass range [0, 360)."""
    return deg % 360.0


def signed_compass_delta(target_deg: float, current_deg: float) -> float:
    """Smallest signed angular delta from current to target, in (-180, 180].

    Positive results indicate a clockwise rotation; negative results are
    counter-clockwise. Useful for circular averaging without 0/360 wrap-around.
    """
    raw = (target_deg - current_deg) % 360.0
    return raw if raw <= 180.0 else raw - 360.0


# ===========================================================================
# Position advection
# ===========================================================================


def haversine_step(
    longitude: float,
    latitude: float,
    east_km: float,
    north_km: float,
) -> Tuple[float, float]:
    """Advance (longitude, latitude) by (east_km, north_km) in equirectangular
    approximation.

    Longitude is wrapped to (-180, 180]. Latitude is clamped to [-90, 90]
    (a defensive guard — at typhoon-relevant latitudes the storm will never
    approach the poles, but Phase 1 trajectories must remain valid even
    under noisy regimes).
    """
    lat_rad = math.radians(latitude)
    # Avoid division by zero exactly at the pole; clamp the cosine floor.
    cos_lat = max(math.cos(lat_rad), 1e-6)

    d_lat_deg = math.degrees(north_km / EARTH_RADIUS_KM)
    d_lon_deg = math.degrees(east_km / (EARTH_RADIUS_KM * cos_lat))

    new_lat = max(-90.0, min(90.0, latitude + d_lat_deg))
    new_lon = longitude + d_lon_deg
    # Wrap longitude into (-180, 180].
    new_lon = ((new_lon + 180.0) % 360.0) - 180.0
    return new_lon, new_lat


# ===========================================================================
# Motion update — spec eq. (5)
# ===========================================================================


def update_motion(
    state: TyphoonState,
    params: MotionParams,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> Tuple[float, float]:
    """Sample the next translation speed and heading.

    Applies persistence-plus-regime-target means, then adds Gaussian noise.
    Above the recurvature latitude, NW_RECURVER and SHARP_RECURVE regimes
    apply an additive northward bias bounded by recurvature_bias_deg_per_step.

    Args:
        state: current latent state
        params: catchment motion parameters
        rng: random generator
        dt_hours: step length (hours). Noise variance scales linearly with dt
            so std scales with sqrt(dt).

    Returns:
        (new_speed_kmh, new_heading_deg)
    """
    regime = state.regime

    # --- Speed: persistence around regime climatological mean ---
    mean_speed = params.mean_speed_kmh[regime]
    sigma_speed = params.sigma_speed_kmh[regime] * math.sqrt(dt_hours)
    mu_u = params.speed_persistence * state.translation_speed_kmh + (
        1.0 - params.speed_persistence
    ) * mean_speed
    new_speed = float(rng.normal(mu_u, sigma_speed))
    # Speed must be non-negative; a reverse-moving storm is unphysical here.
    new_speed = max(0.0, new_speed)

    # --- Heading: circular persistence + optional recurvature bias ---
    mean_heading = params.mean_heading_deg[regime]
    # Apply persistence using a signed-delta toward the regime mean so we
    # don't accidentally short-cross the compass seam (e.g. 350 -> 10).
    delta_to_target = signed_compass_delta(mean_heading, state.heading_deg)
    mu_psi = state.heading_deg + (1.0 - params.heading_persistence) * delta_to_target

    # Recurvature bias: pull heading toward 0 (north) when conditions met.
    if regime in RECURVATURE_REGIMES and state.latitude > params.recurvature_latitude:
        delta_to_north = signed_compass_delta(0.0, mu_psi)
        bias_step = min(abs(delta_to_north), params.recurvature_bias_deg_per_step * dt_hours)
        if delta_to_north != 0.0:
            mu_psi = mu_psi + math.copysign(bias_step, delta_to_north)

    sigma_heading = params.sigma_heading_deg[regime] * math.sqrt(dt_hours)
    new_heading = float(rng.normal(mu_psi, sigma_heading))
    new_heading = wrap_compass_degrees(new_heading)

    return new_speed, new_heading


# ===========================================================================
# Position update — spec eqs. (6) and (7)
# ===========================================================================


def update_position(
    state: TyphoonState,
    speed_kmh: float,
    heading_deg: float,
    dt_hours: float = 1.0,
) -> Tuple[float, float]:
    """Advance position by (speed * dt) in the heading direction.

    Compass heading is converted to mathematical angle (East = 0, CCW positive)
    so that dx = u * dt * cos and dy = u * dt * sin describe (East, North)
    displacement in kilometres.
    """
    # Compass to math: math_angle = 90 - compass.
    math_rad = math.radians(90.0 - heading_deg)
    distance_km = speed_kmh * dt_hours
    east_km = distance_km * math.cos(math_rad)
    north_km = distance_km * math.sin(math_rad)
    return haversine_step(state.longitude, state.latitude, east_km, north_km)


# ===========================================================================
# Intensity update — spec eqs. (8) and (9)
# ===========================================================================


def update_wind(
    state: TyphoonState,
    params: IntensityParams,
    land_flag: bool,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> float:
    """Update V_max given the (end-of-step) land flag.

    Over water (spec eq. 8): V_t ~ N(V_{t-1} + drift * dt, (sigma * sqrt(dt))^2)
    Over land  (spec eq. 9): V_t = V_{t-1} * exp(-k_land * dt)

    Result is clamped to [0, +inf).
    """
    if land_flag:
        v_new = state.v_max_ms * math.exp(-params.k_land_per_hour * dt_hours)
    else:
        mean = state.v_max_ms + params.drift_ms_per_hour * dt_hours
        std = params.sigma_ms_per_hour * math.sqrt(dt_hours)
        v_new = float(rng.normal(mean, std))
    return max(0.0, v_new)


# ===========================================================================
# Size update — spec eq. (10)
# ===========================================================================


def update_size(
    state: TyphoonState,
    new_v_max_ms: float,
    params: SizeParams,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> Tuple[float, float]:
    """Mean-reverting log-space update of (R_max, R_outer).

    Each radius is updated as:
        log(R_t) = log(R_{t-1})
                 + rate * dt * (log(R_target) - log(R_{t-1}))
                 + N(0, (sigma * sqrt(dt))^2)

    where log(R_target) is a linear function of log(V_max). The invariant
    R_max < R_outer is enforced post-update by widening R_outer when
    collisions occur.
    """
    log_v = math.log(max(new_v_max_ms, 1.0))   # guard near zero
    log_rmax_target = params.r_max_intercept_log_km + params.r_max_v_coef * log_v
    log_router_target = params.r_outer_intercept_log_km + params.r_outer_v_coef * log_v

    log_rmax_prev = math.log(max(state.r_max_km, 1.0))
    log_router_prev = math.log(max(state.r_outer_km, 1.0))

    pull = params.mean_reversion_rate * dt_hours
    sigma_rmax = params.r_max_sigma_log * math.sqrt(dt_hours)
    sigma_router = params.r_outer_sigma_log * math.sqrt(dt_hours)

    log_rmax_new = (
        log_rmax_prev
        + pull * (log_rmax_target - log_rmax_prev)
        + float(rng.normal(0.0, sigma_rmax))
    )
    log_router_new = (
        log_router_prev
        + pull * (log_router_target - log_router_prev)
        + float(rng.normal(0.0, sigma_router))
    )

    r_max_new = math.exp(log_rmax_new)
    r_outer_new = math.exp(log_router_new)

    if r_outer_new <= r_max_new:
        r_outer_new = r_max_new * 1.5

    return r_max_new, r_outer_new


# ===========================================================================
# One-step propagator
# ===========================================================================


def step(
    state: TyphoonState,
    config: CatchmentTyphoonConfig,
    rng: np.random.Generator,
    dt_hours: float = 1.0,
) -> TyphoonState:
    """Advance the latent state by dt_hours.

    Order of operations:
      1. Sample new motion (u_t, psi_t) using the regime-conditioned model.
      2. Advance position using the new motion.
      3. Evaluate the land flag at the new position.
      4. Update V_max conditional on the new land flag.
      5. Update (R_max, R_outer) conditional on the new V_max.

    The regime is fixed at genesis in Phase 1 and is propagated unchanged.

    Args:
        state: previous latent state (time t-1)
        config: catchment configuration
        rng: random generator
        dt_hours: step length (hours), default 1.0

    Returns:
        New TyphoonState at time t.
    """
    new_speed, new_heading = update_motion(state, config.motion, rng, dt_hours)
    new_lon, new_lat = update_position(state, new_speed, new_heading, dt_hours)
    new_land_flag = bool(config.land_mask(new_lon, new_lat))
    new_v_max = update_wind(state, config.intensity, new_land_flag, rng, dt_hours)
    new_r_max, new_r_outer = update_size(state, new_v_max, config.size, rng, dt_hours)

    return TyphoonState(
        longitude=new_lon,
        latitude=new_lat,
        translation_speed_kmh=new_speed,
        heading_deg=new_heading,
        v_max_ms=new_v_max,
        r_max_km=new_r_max,
        r_outer_km=new_r_outer,
        regime=state.regime,
        land_flag=new_land_flag,
        time_hours=state.time_hours + dt_hours,
    )


def advance(
    state: TyphoonState,
    config: CatchmentTyphoonConfig,
    rng: np.random.Generator,
    n_steps: int,
    dt_hours: float = 1.0,
) -> List[TyphoonState]:
    """Apply step() n_steps times, returning the full forward trajectory.

    The returned list contains n_steps elements (the initial state is NOT
    included; callers that need the genesis state should prepend it).
    """
    if n_steps < 0:
        raise ValueError(f"n_steps must be non-negative, got {n_steps}")
    trajectory: List[TyphoonState] = []
    current = state
    for _ in range(n_steps):
        current = step(current, config, rng, dt_hours)
        trajectory.append(current)
    return trajectory
