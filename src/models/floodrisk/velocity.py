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
Water velocity and lateral flood propagation model.

Manning's equation for overbank flow velocity, travel time from gauge
to property, distance-based attenuation, and property-level hydrograph
construction from gauge timeseries.
"""

import math
from typing import Dict, List

from config.models import (
    DEFAULT_RETENTION_LENGTH,
    DEFAULT_RECESSION_FACTOR,
    DEFAULT_ROUGHNESS,
    MIN_SLOPE,
)


def compute_manning_velocity(depth_m: float, slope: float,
                              roughness: float = DEFAULT_ROUGHNESS) -> float:
    """
    Compute lateral flood velocity using Manning's equation.

    v = (1/n) * R^(2/3) * S^(1/2)

    For shallow overbank flow the hydraulic radius R ≈ depth.

    Args:
        depth_m: Water depth in meters (must be > 0)
        slope: Energy slope (dimensionless, e.g. 0.005)
        roughness: Manning's n coefficient (default 0.04 for urban floodplain)

    Returns:
        Velocity in m/s (0 if depth <= 0)
    """
    if depth_m <= 0 or roughness <= 0:
        return 0.0

    slope = max(abs(slope), MIN_SLOPE)
    return (1.0 / roughness) * (depth_m ** (2.0 / 3.0)) * math.sqrt(slope)


def compute_travel_time(distance_m: float, depth_m: float,
                         slope: float,
                         roughness: float = DEFAULT_ROUGHNESS) -> float:
    """
    Compute travel time for flood front to reach a property.

    Args:
        distance_m: Lateral distance from gauge/river to property (meters)
        depth_m: Representative water depth for velocity calculation
        slope: Ground slope between gauge and property

    Returns:
        Travel time in hours (float). Returns inf if velocity is zero.
    """
    velocity = compute_manning_velocity(depth_m, slope, roughness)
    if velocity <= 0:
        return float('inf')
    return (distance_m / velocity) / 3600.0


def compute_retention(distance_m: float,
                       length: float = DEFAULT_RETENTION_LENGTH) -> float:
    """
    Compute distance-based retention factor for water surface elevation.

    Pure exponential decay from distance 0: retention = exp(-d / length).
    With the default 3 km e-folding length, a property 600 m from the
    gauge retains ~82 % of the flood signal; at 2 km ~51 %; at 5 km ~19 %.

    Args:
        distance_m: Distance from river/gauge in meters
        length: Characteristic retention length in meters (default 3000)

    Returns:
        Retention factor between 0 and 1 (1 = full signal, 0 = no signal)
    """
    if distance_m <= 0:
        return 1.0
    if length <= 0:
        return 0.0
    return math.exp(-distance_m / length)


# Backwards compatibility alias
compute_attenuation = compute_retention


def compute_slope(gauge_elevation: float, property_elevation: float,
                   distance_m: float) -> float:
    """
    Compute ground slope between gauge and property.

    Args:
        gauge_elevation: Gauge ground level (meters AOD)
        property_elevation: Property ground level (meters AOD)
        distance_m: Horizontal distance between them (meters)

    Returns:
        Slope (dimensionless), clamped to MIN_SLOPE minimum
    """
    if distance_m <= 0:
        return MIN_SLOPE
    slope = abs(gauge_elevation - property_elevation) / distance_m
    return max(slope, MIN_SLOPE)


def build_property_hydrograph(gauge_readings: List[Dict],
                               peak_wse: float,
                               travel_time_hrs: float,
                               retention: float,
                               prop_elevation: float,
                               floor_level: float,
                               recession_factor: float = DEFAULT_RECESSION_FACTOR
                               ) -> List[Dict]:
    """
    Build a property-level hydrograph from gauge timeseries.

    Takes the gauge's hourly readings, shifts by travel time, and
    computes flood depth at the property accounting for elevation
    and floor level (step).  Retention is applied by the caller
    before computing peak_wse; it is accepted here only for API
    compatibility and logging but is NOT re-applied to the WSE.

    Args:
        gauge_readings: List of dicts with 'hour' and 'water_level_m' keys
            (typically 168 hourly readings from flood simulation)
        peak_wse: Peak water surface elevation at the property location
            (already IDW-interpolated; retention already applied by caller)
        travel_time_hrs: Hours for flood front to reach property
        retention: Distance retention factor (0-1). NOT applied here;
            retained for API compatibility.
        prop_elevation: Property ground level (meters AOD)
        floor_level: Property floor level / step height (meters)
        recession_factor: Multiplier for recession limb duration (default 1.5)

    Returns:
        List of dicts with keys:
            hour, wse_m, depth_m, flooded (bool)
    """
    if not gauge_readings:
        return []

    n_hours = len(gauge_readings)

    # Extract gauge water levels and find the gauge peak
    gauge_levels = []
    for r in gauge_readings:
        gauge_levels.append(r.get('water_level_m', r.get('level', 0.0)))

    gauge_peak = max(gauge_levels) if gauge_levels else 0.0
    gauge_base = min(gauge_levels) if gauge_levels else 0.0
    if gauge_peak <= 0:
        return [{'hour': h, 'wse_m': 0.0, 'depth_m': 0.0, 'flooded': False}
                for h in range(n_hours)]

    gauge_rise = gauge_peak - gauge_base

    # Find the hour of gauge peak
    peak_hour = gauge_levels.index(gauge_peak)

    # Build the property hydrograph
    result = []
    flood_threshold = prop_elevation + floor_level

    for hour in range(n_hours):
        # Shift time by travel delay
        source_time = hour - travel_time_hrs

        if source_time < 0:
            # Flood front hasn't arrived yet — water at normal river level
            result.append({
                'hour': hour,
                'wse_m': round(gauge_base, 4),
                'depth_m': 0.0,
                'flooded': False
            })
            continue

        # Determine which gauge reading to sample from
        # On rising limb: direct mapping
        # On recession limb: stretch time by recession_factor (slower drainage)
        shifted_peak_hour = peak_hour + travel_time_hrs

        if hour <= shifted_peak_hour:
            # Rising limb — direct time shift
            gauge_idx = int(round(source_time))
        else:
            # Recession limb — slow down by recession_factor
            hours_past_peak = hour - shifted_peak_hour
            recession_source = peak_hour + (hours_past_peak / recession_factor)
            gauge_idx = int(round(recession_source))

        gauge_idx = max(0, min(gauge_idx, n_hours - 1))

        # Scale gauge level to property WSE based on fractional rise above base
        gauge_level = gauge_levels[gauge_idx]
        if gauge_rise > 0:
            scale = (gauge_level - gauge_base) / gauge_rise
        else:
            scale = 0.0

        # Retention already applied by caller (_build_flood_event) when
        # computing water_at_property; do NOT multiply again here.
        prop_wse = gauge_base + (peak_wse - gauge_base) * scale

        # Flood depth above floor level
        depth = max(0.0, prop_wse - flood_threshold)
        flooded = depth > 0

        result.append({
            'hour': hour,
            'wse_m': round(prop_wse, 4),
            'depth_m': round(depth, 4),
            'flooded': flooded
        })

    return result
