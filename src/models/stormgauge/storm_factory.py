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
Storm creation helpers.

Factory function for creating storms with generated track points,
and loader for gauge configurations from portfolio JSON files.
"""

import json
import math
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    IntensityProfile,
    Storm,
    TrackPoint,
)


def create_storm(
    track_start: Tuple[float, float],
    track_end: Tuple[float, float],
    storm_id: Optional[str] = None,
    name: str = "Storm",
    start_time: Optional[datetime] = None,
    peak_intensity: float = 50.0,
    footprint_km: float = 40.0,
    duration_hours: float = 24.0,
    decay_kernel: DecayKernel = DecayKernel.GAUSSIAN,
    decay_parameter: float = 0.5,
    intensity_profile: IntensityProfile = IntensityProfile.TRIANGULAR,
    num_track_points: int = 25,
) -> Storm:
    """Create a storm with generated track points.

    ``track_start`` and ``track_end`` are required (lon, lat) tuples
    describing the storm's spatial trajectory. Callers should source
    them from the active catchment's storm module —
    ``from catch.<catchment>.storm import TRACK_START, TRACK_END`` —
    rather than hardcoding values.

    Args:
        track_start: (longitude, latitude) of track start
        track_end: (longitude, latitude) of track end
        storm_id: Unique ID (auto-generated if None)
        name: Storm name
        start_time: Start datetime (defaults to now)
        peak_intensity: Maximum intensity (0-100)
        footprint_km: Precipitation field width in km
        duration_hours: Total storm duration
        decay_kernel: Spatial decay type
        decay_parameter: Decay kernel parameter
        intensity_profile: How intensity varies along track
        num_track_points: Number of points to generate along track

    Returns:
        Configured Storm object
    """
    import uuid

    if storm_id is None:
        storm_id = f"STORM-{uuid.uuid4().hex[:8]}"

    if start_time is None:
        start_time = datetime.now()

    # Generate track points
    track = []
    for i in range(num_track_points):
        t_frac = i / (num_track_points - 1)
        t_hours = t_frac * duration_hours

        lon = track_start[0] + t_frac * (track_end[0] - track_start[0])
        lat = track_start[1] + t_frac * (track_end[1] - track_start[1])

        if intensity_profile == IntensityProfile.TRIANGULAR:
            if t_frac <= 0.5:
                intensity = peak_intensity * (t_frac / 0.5)
            else:
                intensity = peak_intensity * (1 - (t_frac - 0.5) / 0.5)

        elif intensity_profile == IntensityProfile.GAUSSIAN:
            intensity = peak_intensity * math.exp(-((t_frac - 0.5) ** 2) / (2 * 0.15 ** 2))

        elif intensity_profile == IntensityProfile.BETA:
            intensity = peak_intensity * 4 * t_frac * (1 - t_frac)

        else:
            intensity = peak_intensity * t_frac

        track.append(TrackPoint(
            longitude=lon,
            latitude=lat,
            time_hours=t_hours,
            intensity=intensity,
        ))

    # Calculate speed
    start_lon, start_lat = track_start
    end_lon, end_lat = track_end

    R = 6371
    dlat = math.radians(end_lat - start_lat)
    dlon = math.radians(end_lon - start_lon)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(dlon / 2) ** 2
    distance_km = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    speed_kmh = distance_km / duration_hours

    return Storm(
        storm_id=storm_id,
        name=name,
        start_time=start_time,
        duration_hours=duration_hours,
        track=track,
        peak_intensity=peak_intensity,
        footprint_km=footprint_km,
        decay_kernel=decay_kernel,
        decay_parameter=decay_parameter,
        intensity_profile=intensity_profile,
        speed_kmh=speed_kmh,
    )


def load_gauges_from_portfolio(portfolio_path: Path) -> List[GaugeConfig]:
    """Load gauge configurations from a gauge portfolio JSON file."""
    with open(portfolio_path, 'r') as f:
        data = json.load(f)

    gauges = []
    for entry in data.get("flood_gauges", []):
        gauges.append(GaugeConfig.from_gauge_portfolio(entry))

    return gauges
