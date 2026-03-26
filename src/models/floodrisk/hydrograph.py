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
Per-pulse hydrograph superposition model (v2.2).

Builds compound property hydrographs from individual storm pulses using
gamma-shaped templates, antecedent saturation scaling, linear superposition,
and flow-path infiltration.  Replaces the single-peak / single-shape approach
in velocity.build_property_hydrograph() for multi-storm sequences.
"""

import math
from typing import Dict, List, Optional

import numpy as np

from config.models import (
    HYDRO_ALPHA,
    SATURATION_BETA,
    SATURATION_P0_MM,
    INFILTRATION_RATE_PER_HOUR,
    INFILTRATION_YMAX_REF_M,
    DEFAULT_IMPERV_FRACTION,
    SUPERPOSITION_CAP_FACTOR,
    STORM_SIMULATION_HOURS,
)
from .velocity import compute_slope, compute_travel_time, compute_retention


# ---------------------------------------------------------------------------
# 1. Gamma shape template
# ---------------------------------------------------------------------------

def gamma_shape(u: float, alpha: float) -> float:
    """Dimensionless gamma-like hydrograph shape, normalised to peak = 1.

    Raw formula: f(u) = (u/alpha)^alpha * exp(alpha - u/alpha)
    Peak at u = alpha^2 with raw value alpha^alpha.
    Normalised: phi(u) = f(u) / alpha^alpha.

    Args:
        u: Dimensionless time fraction in [0, 1].
        alpha: Shape parameter (0 < alpha <= 1).
            Small alpha → fast rise, long tail (flashy).
            Large alpha → broad symmetric peak.

    Returns:
        Shape value in [0, 1].  Zero outside (0, 1].
    """
    if u <= 0 or u > 1 or alpha <= 0:
        return 0.0
    ratio = u / alpha
    # f(u) = exp(alpha * ln(u/alpha) + alpha - u/alpha)
    # Normalise by dividing by alpha^alpha = exp(alpha * ln(alpha))
    log_val = alpha * math.log(ratio) + alpha - ratio
    log_norm = alpha * math.log(alpha)  # log of peak value
    return math.exp(log_val - log_norm)


def gamma_shape_array(hours: np.ndarray, start_hour: float,
                      duration_hours: float, alpha: float) -> np.ndarray:
    """Vectorised gamma shape over an array of absolute hours.

    Args:
        hours: 1-D array of hour indices (e.g. 0..167).
        start_hour: Pulse start time (hours).
        duration_hours: Pulse duration (hours, > 0).
        alpha: Gamma shape parameter.

    Returns:
        Array same shape as *hours* with values in [0, 1].
    """
    if duration_hours <= 0 or alpha <= 0:
        return np.zeros_like(hours, dtype=float)

    u = (hours - start_hour) / duration_hours
    result = np.zeros_like(hours, dtype=float)
    mask = (u > 0) & (u <= 1)
    um = u[mask]
    ratio = um / alpha
    log_val = alpha * np.log(ratio) + alpha - ratio
    log_norm = alpha * math.log(alpha)
    result[mask] = np.exp(log_val - log_norm)
    return result


# ---------------------------------------------------------------------------
# 2. Per-pulse gauge hydrograph
# ---------------------------------------------------------------------------

def build_pulse_gauge_hydrograph(base_level: float, peak_m: float,
                                 start_hour: float, duration_hours: float,
                                 alpha: float,
                                 n_hours: int = STORM_SIMULATION_HOURS,
                                 ) -> np.ndarray:
    """Build a single-pulse hydrograph at the gauge using the gamma template.

    WSE_i(h) = base + (peak - base) * phi((h - start) / duration)

    Args:
        base_level: Gauge base water level (m AOD).
        peak_m: Pulse peak water surface elevation (m AOD).
        start_hour: Pulse start hour within the 168h window.
        duration_hours: Pulse duration (hours).
        alpha: Gamma shape parameter for this storm type.
        n_hours: Total simulation hours (default 168).

    Returns:
        np.ndarray of shape (n_hours,) with WSE values.
    """
    hours = np.arange(n_hours, dtype=float)
    shape = gamma_shape_array(hours, start_hour, duration_hours, alpha)
    exceedance = max(0.0, peak_m - base_level)
    return base_level + exceedance * shape


# ---------------------------------------------------------------------------
# 3. Antecedent saturation
# ---------------------------------------------------------------------------

def compute_saturation_factor(antecedent_precip_mm: float,
                              beta: float = SATURATION_BETA,
                              p0: float = SATURATION_P0_MM) -> float:
    """Compute saturation multiplier for a pulse's peak exceedance.

    s_i = 1 + beta * log(1 + A_i / P_0)

    Later pulses in a sequence get amplified because earlier rainfall
    has saturated the catchment.

    Args:
        antecedent_precip_mm: Cumulative precipitation from prior pulses (mm).
        beta: Log-sensitivity parameter (default 0.2).
        p0: Reference precipitation (mm, default 50).

    Returns:
        Multiplier >= 1.0.
    """
    if antecedent_precip_mm <= 0 or p0 <= 0:
        return 1.0
    return 1.0 + beta * math.log(1.0 + antecedent_precip_mm / p0)


# ---------------------------------------------------------------------------
# 4. Superposition
# ---------------------------------------------------------------------------

def superimpose_pulses(base_level: float,
                       pulse_arrays: List[np.ndarray],
                       cap: Optional[float] = None) -> np.ndarray:
    """Superimpose multiple pulse hydrographs via linear addition.

    WSE(h) = base + sum_i (pulse_i(h) - base)

    Args:
        base_level: Gauge base water level (m AOD).
        pulse_arrays: List of per-pulse WSE arrays (each shape (n_hours,)).
        cap: Optional absolute cap on exceedance above base (m).

    Returns:
        Combined WSE array of same shape as input arrays.
    """
    if not pulse_arrays:
        n = STORM_SIMULATION_HOURS
        return np.full(n, base_level)

    n = len(pulse_arrays[0])
    total_exceedance = np.zeros(n, dtype=float)
    for arr in pulse_arrays:
        total_exceedance += np.maximum(0.0, arr - base_level)

    if cap is not None and cap > 0:
        np.clip(total_exceedance, 0, cap, out=total_exceedance)

    return base_level + total_exceedance


# ---------------------------------------------------------------------------
# 5. Flow-path infiltration
# ---------------------------------------------------------------------------

def apply_infiltration(raw_depth: np.ndarray,
                       kappa: float = INFILTRATION_RATE_PER_HOUR,
                       y_max: float = INFILTRATION_YMAX_REF_M,
                       f_imperv: float = DEFAULT_IMPERV_FRACTION,
                       dt: float = 1.0) -> np.ndarray:
    """Apply time-varying infiltration loss to a depth series.

    Tracks cumulative infiltrated depth Y_inf.  Infiltration capacity
    decreases as the soil saturates.  The fraction of water *lost* to
    infiltration at each step is proportional to remaining capacity:

        loss(t) = min(kappa * raw_depth * dt,  Y_max - Y_inf)
        depth(t) = raw_depth(t) - loss(t)

    Once Y_inf reaches Y_max the ground is fully saturated and all
    subsequent water passes through unchanged.

    Y_max = (1 - f_imperv) * y_max_ref.

    Args:
        raw_depth: Raw flood depth above ground (m), shape (n_hours,).
        kappa: Hourly infiltration rate constant (1/hr).
        y_max: Reference max infiltrable depth for fully pervious (m).
        f_imperv: Fraction impervious surface (0-1).
        dt: Time step in hours.

    Returns:
        Adjusted depth array, same shape as input.
    """
    effective_ymax = (1.0 - f_imperv) * y_max
    if effective_ymax <= 0 or kappa <= 0:
        # Fully impervious or no infiltration → no loss
        return raw_depth.copy()

    result = np.empty_like(raw_depth)
    y_inf = 0.0

    for i in range(len(raw_depth)):
        d = raw_depth[i]
        if d > 0 and y_inf < effective_ymax:
            # Infiltration loss limited by remaining capacity
            loss = min(kappa * d * dt, effective_ymax - y_inf)
            y_inf += loss
            result[i] = max(0.0, d - loss)
        else:
            # Ground saturated or no water — pass through
            result[i] = d

    return result


# ---------------------------------------------------------------------------
# 6. Orchestrator: compound property hydrograph
# ---------------------------------------------------------------------------

def build_compound_property_hydrograph(
    pulse_peaks: List[Dict],
    sequence_type: str,
    base_level: float,
    gauge_elevation: float,
    prop_elevation: float,
    floor_level: float,
    travel_time_hrs: float,
    retention: float,
    f_imperv: float = DEFAULT_IMPERV_FRACTION,
    cap: Optional[float] = None,
    n_hours: int = STORM_SIMULATION_HOURS,
) -> List[Dict]:
    """Build a compound property hydrograph from per-pulse peaks.

    Pipeline:
      1. For each pulse, compute saturation-adjusted peak
      2. Build gamma-shaped gauge hydrograph per pulse
      3. Superimpose all pulses at the gauge
      4. Time-shift by travel time
      5. Compute raw depth above property flood threshold
      6. Apply infiltration
      7. Return hourly records

    Args:
        pulse_peaks: List of dicts, each with keys:
            storm_index, peak_m, start_hour, duration_hours, precip_mm
        sequence_type: One of 'isolated', 'doublet', 'cluster', 'persistent'.
        base_level: Gauge base water level (m AOD).
        gauge_elevation: Gauge ground elevation (m AOD).
        prop_elevation: Property ground elevation (m AOD).
        floor_level: Property floor step height (m).
        travel_time_hrs: Hours for flood front to reach property.
        retention: Distance retention factor (0-1).
        f_imperv: Fraction impervious surface (0-1).
        cap: Optional absolute cap on exceedance above base (m).
        n_hours: Simulation window hours (default 168).

    Returns:
        List of dicts with keys: hour, wse_m, depth_m, flooded.
    """
    alpha = HYDRO_ALPHA.get(sequence_type, 0.3)

    # Sort pulses by start_hour to compute cumulative antecedent precip
    sorted_pulses = sorted(pulse_peaks, key=lambda p: p.get('start_hour', 0))

    # Step 1-2: build per-pulse gauge hydrographs with saturation
    pulse_arrays = []
    cumulative_precip = 0.0

    for pulse in sorted_pulses:
        peak_m = pulse.get('peak_m', base_level)
        start_h = pulse.get('start_hour', 0.0)
        dur_h = pulse.get('duration_hours', 24.0)
        precip = pulse.get('precip_mm', 0.0)

        # Saturation amplifies exceedance above base
        sat = compute_saturation_factor(cumulative_precip)
        adjusted_peak = base_level + (peak_m - base_level) * sat

        arr = build_pulse_gauge_hydrograph(
            base_level, adjusted_peak, start_h, dur_h, alpha, n_hours
        )
        pulse_arrays.append(arr)
        cumulative_precip += precip

    # Step 3: superimpose at gauge
    gauge_wse = superimpose_pulses(base_level, pulse_arrays, cap=cap)

    # Step 4: time-shift and apply retention + elevation
    flood_threshold = prop_elevation + floor_level
    height_diff = max(0.0, prop_elevation - gauge_elevation)
    prop_threshold_above_gauge = height_diff + floor_level

    hours = np.arange(n_hours, dtype=float)
    # Shift: property hour t corresponds to gauge hour (t - travel_time)
    shift = int(round(travel_time_hrs))

    # Step 5: compute raw depth at property
    raw_depth = np.zeros(n_hours, dtype=float)
    for t in range(n_hours):
        src = t - shift
        if src < 0 or src >= n_hours:
            continue
        water_above_gauge = max(0.0, gauge_wse[src] - gauge_elevation)
        water_at_property = water_above_gauge * retention
        depth_above_floor = water_at_property - prop_threshold_above_gauge
        if depth_above_floor > 0:
            raw_depth[t] = depth_above_floor

    # Step 6: apply infiltration
    adjusted_depth = apply_infiltration(raw_depth, f_imperv=f_imperv)

    # Step 7: build output records
    result = []
    for t in range(n_hours):
        d = round(float(adjusted_depth[t]), 4)
        # Reconstruct WSE at property for the record
        wse = round(flood_threshold + d, 4) if d > 0 else round(float(
            gauge_elevation + raw_depth[t] + prop_threshold_above_gauge
            if raw_depth[t] > 0 else base_level
        ), 4)
        result.append({
            'hour': t,
            'wse_m': wse,
            'depth_m': d,
            'flooded': d > 0,
        })

    return result
