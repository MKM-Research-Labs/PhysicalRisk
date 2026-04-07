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

"""Compound property hydrograph orchestrator."""

import logging
from typing import Dict, List, Optional

import numpy as np

from config.models import (
    HYDRO_ALPHA,
    DEFAULT_IMPERV_FRACTION,
    STORM_SIMULATION_HOURS,
)
from .gamma import gamma_shape_array
from .pulse import build_pulse_gauge_hydrograph
from .saturation import compute_saturation_factor, superimpose_pulses
from .infiltration import apply_infiltration


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
    severe_level: float = 0.0,
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
        # gauge_wse values are stage readings; flood depth at gauge =
        # reading − severe_level (flooding starts at severe threshold).
        water_above_gauge = max(0.0, gauge_wse[src] - severe_level)
        water_at_property = water_above_gauge * retention
        depth_above_floor = water_at_property - prop_threshold_above_gauge
        if depth_above_floor > 0:
            raw_depth[t] = depth_above_floor

    # Step 6: infiltration removed — the distance retention factor already
    # accounts for aggregate losses (friction, storage, infiltration) between
    # the gauge and property.  Applying explicit infiltration on top of the
    # bankfull threshold and retention decay is double-counting.
    # See: Flood Propagation Code Review, Section 4 (Double-Counting Problem).
    adjusted_depth = raw_depth

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
