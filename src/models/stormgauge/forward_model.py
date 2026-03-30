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
Storm gauge forward model.

Computes gauge water level responses given storm parameters.
Maps storm characteristics (track, intensity, footprint) to
water level timeseries at each gauge location.
"""

import math
from typing import List, Tuple

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    GaugeResponse,
    Storm,
    TrackPoint,
)


class StormGaugeModel:
    """
    Forward model: Storm parameters -> Gauge water level responses.

    The model computes water level at each gauge based on:
    1. Storm track proximity (distance from gauge to nearest track point)
    2. Storm intensity at that track point
    3. Spatial decay based on distance and footprint
    4. Gauge-specific transfer function (intensity -> water level)

    Parameters:
        intensity_to_level_scale: Multiplier from intensity to water level contribution
        time_resolution_hours: Time step for simulation
        response_lag_hours: Lag between storm passage and peak gauge response
        response_decay_hours: How quickly gauge level returns to normal after storm
    """

    def __init__(
        self,
        intensity_to_level_scale: float = 0.1,
        time_resolution_hours: float = 0.5,
        response_lag_hours: float = 2.0,
        response_decay_hours: float = 12.0,
    ):
        self.intensity_to_level_scale = intensity_to_level_scale
        self.time_resolution_hours = time_resolution_hours
        self.response_lag_hours = response_lag_hours
        self.response_decay_hours = response_decay_hours

    def haversine_km(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """Calculate distance in km between two points using Haversine formula."""
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def compute_decay(
        self,
        distance_km: float,
        footprint_km: float,
        kernel: DecayKernel,
        decay_param: float,
    ) -> float:
        """
        Compute spatial decay factor based on distance from storm track.

        Returns value in [0, 1] where 1 = on track, 0 = far away.
        """
        if distance_km <= 0:
            return 1.0

        d_norm = distance_km / footprint_km

        if kernel == DecayKernel.GAUSSIAN:
            sigma = decay_param
            return math.exp(-0.5 * (d_norm / sigma) ** 2)

        elif kernel == DecayKernel.EXPONENTIAL:
            lam = decay_param
            return math.exp(-d_norm / lam)

        elif kernel == DecayKernel.LINEAR:
            r = decay_param
            return max(0.0, 1.0 - d_norm / r)

        return 0.0

    def find_nearest_track_point(
        self,
        gauge_lon: float,
        gauge_lat: float,
        track: List[TrackPoint],
    ) -> Tuple[TrackPoint, float]:
        """
        Find the track point nearest to the gauge and return distance.

        Returns:
            Tuple of (nearest TrackPoint, distance in km)
        """
        min_dist = float('inf')
        nearest = track[0]

        for point in track:
            dist = self.haversine_km(gauge_lon, gauge_lat, point.longitude, point.latitude)
            if dist < min_dist:
                min_dist = dist
                nearest = point

        return nearest, min_dist

    def compute_intensity_at_gauge(
        self,
        time_hours: float,
        gauge_lon: float,
        gauge_lat: float,
        storm: Storm,
    ) -> float:
        """
        Compute storm intensity experienced at gauge location at given time.

        Interpolates storm position along track based on time, then applies
        spatial decay based on distance.
        """
        if not storm.track:
            return 0.0

        # Find track points bracketing current time
        prev_point = storm.track[0]
        next_point = storm.track[-1]

        for i, point in enumerate(storm.track):
            if point.time_hours <= time_hours:
                prev_point = point
                if i + 1 < len(storm.track):
                    next_point = storm.track[i + 1]
            else:
                next_point = point
                break

        # Interpolate storm position and intensity
        if next_point.time_hours == prev_point.time_hours:
            t_frac = 0.0
        else:
            t_frac = (time_hours - prev_point.time_hours) / (next_point.time_hours - prev_point.time_hours)
            t_frac = max(0.0, min(1.0, t_frac))

        storm_lon = prev_point.longitude + t_frac * (next_point.longitude - prev_point.longitude)
        storm_lat = prev_point.latitude + t_frac * (next_point.latitude - prev_point.latitude)
        storm_intensity = prev_point.intensity + t_frac * (next_point.intensity - prev_point.intensity)

        # Compute distance from gauge to current storm position
        distance_km = self.haversine_km(gauge_lon, gauge_lat, storm_lon, storm_lat)

        # Apply spatial decay
        decay = self.compute_decay(
            distance_km,
            storm.footprint_km,
            storm.decay_kernel,
            storm.decay_parameter,
        )

        return storm_intensity * decay

    def intensity_to_level(
        self,
        intensity: float,
        gauge: GaugeConfig,
    ) -> float:
        """
        Convert storm intensity (0-100) to water level contribution.

        The mapping is calibrated such that:
        - Intensity ~40 approaches flood alert
        - Intensity ~60-70 approaches flood warning
        - Intensity ~85+ approaches severe warning
        - Intensity 100 reaches historical high

        Returns the water level above base level.
        """
        if intensity <= 0:
            return 0.0

        max_level = gauge.historical_high or (gauge.severe_warning * 1.1)
        level_range = max_level - gauge.base_level

        gamma = 0.8
        normalised = (intensity / 100.0) ** gamma

        level_contribution = normalised * level_range * gauge.sensitivity

        return level_contribution

    def compute_response(
        self,
        storm: Storm,
        gauge: GaugeConfig,
    ) -> GaugeResponse:
        """
        Compute full gauge response to a storm event.

        Simulates both intensity and water level timeseries,
        extracting summary statistics.
        """
        # Generate time points
        num_steps = int(storm.duration_hours / self.time_resolution_hours) + 1
        times = [i * self.time_resolution_hours for i in range(num_steps)]

        # Compute intensity timeseries at gauge
        intensity_ts = []
        for t in times:
            intensity = self.compute_intensity_at_gauge(
                t, gauge.longitude, gauge.latitude, storm
            )
            intensity_ts.append({"time_hours": t, "intensity": intensity})

        # Find peak intensity
        intensities = [p["intensity"] for p in intensity_ts]
        peak_intensity = max(intensities)
        peak_intensity_idx = intensities.index(peak_intensity)
        peak_intensity_time = times[peak_intensity_idx]

        # Convert intensity to water level with lag and decay
        level_ts = []
        current_contribution = 0.0

        for i, t in enumerate(times):
            lag_steps = int(self.response_lag_hours / self.time_resolution_hours)
            lagged_idx = max(0, i - lag_steps)
            lagged_intensity = intensities[lagged_idx]

            target_contribution = self.intensity_to_level(lagged_intensity, gauge)

            decay_rate = self.time_resolution_hours / self.response_decay_hours
            if target_contribution > current_contribution:
                current_contribution += (target_contribution - current_contribution) * min(1.0, decay_rate * 3)
            else:
                current_contribution += (target_contribution - current_contribution) * decay_rate

            level = gauge.base_level + current_contribution
            level_ts.append({"time_hours": t, "level": level})

        # Extract summary statistics
        levels = [p["level"] for p in level_ts]
        peak_level = max(levels)
        peak_idx = levels.index(peak_level)
        peak_time = times[peak_idx]
        peak_exceedance = peak_level - gauge.flood_alert

        dt = self.time_resolution_hours
        duration_alert = sum(dt for l in levels if l >= gauge.flood_alert)
        duration_warning = sum(dt for l in levels if l >= gauge.flood_warning)
        duration_severe = sum(dt for l in levels if l >= gauge.severe_warning)

        accumulation = sum(
            max(0, l - gauge.flood_alert) * dt
            for l in levels
        )

        return GaugeResponse(
            gauge_id=gauge.gauge_id,
            storm_id=storm.storm_id,
            flooded=peak_level >= gauge.flood_alert,
            peak_level=peak_level,
            peak_exceedance=peak_exceedance,
            peak_time_hours=peak_time,
            peak_intensity=peak_intensity,
            peak_intensity_time_hours=peak_intensity_time,
            duration_above_alert=duration_alert,
            duration_above_warning=duration_warning,
            duration_above_severe=duration_severe,
            accumulation=accumulation,
            intensity_timeseries=intensity_ts,
            level_timeseries=level_ts,
        )

    def compute_all_responses(
        self,
        storm: Storm,
        gauges: List[GaugeConfig],
    ) -> List[GaugeResponse]:
        """Compute responses for all gauges."""
        return [self.compute_response(storm, g) for g in gauges]
