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

"""Geometry, spatial decay, and intensity-at-gauge computations."""

import math
from typing import List, Tuple

from ..data_structures import DecayKernel, GaugeConfig, Storm, TrackPoint


class _IntensityMixin:
    """Distance, decay, track interpolation and intensity-to-level mapping."""

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
