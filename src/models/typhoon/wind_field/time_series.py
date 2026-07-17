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

"""Trajectory-level wind-field evaluation — produces WindFieldOutput.

Iterates evaluate_point over each state in a TyphoonTrajectory and
aggregates the time series into the point outputs required by the
wind-field spec p.13:

  - sustained_ms time series
  - peak_sustained_ms and time_of_peak_hours
  - distance_at_peak_km, azimuth_at_peak_deg
  - duration_above_ms per configured threshold

Duration above a threshold is approximated by summing the time
intervals between consecutive samples whose leading sample exceeds the
threshold. The trailing sample contributes no duration. This is a
rectangular approximation; at 1-hour resolution the discretisation
error is small.
"""

from typing import Iterable, List, Optional

from config.typhoon import LandMask, PropertyPoint, WindFieldParams
from models.typhoon.data_structures import TyphoonTrajectory, WindFieldOutput
from models.typhoon.wind_field.point import evaluate_point_with_geometry


__all__ = ["evaluate_time_series", "duration_above_threshold"]


def duration_above_threshold(
    time_hours: List[float],
    values: List[float],
    threshold: float,
) -> float:
    """Rectangular approximation of hours where values > threshold.

    For each consecutive pair (t_i, v_i) -> (t_{i+1}, v_{i+1}), if v_i is
    above the threshold the interval (t_{i+1} - t_i) is added. The final
    sample contributes nothing.
    """
    total = 0.0
    for i in range(len(time_hours) - 1):
        if values[i] > threshold:
            total += time_hours[i + 1] - time_hours[i]
    return total


def evaluate_time_series(
    trajectory: TyphoonTrajectory,
    property_point: PropertyPoint,
    params: WindFieldParams,
    land_mask: LandMask,
    thresholds_ms: Optional[Iterable[float]] = None,
) -> WindFieldOutput:
    """Evaluate the wind-field along a trajectory at a single property point.

    Args:
        trajectory: time-ordered sequence of TyphoonState
        property_point: (property_id, longitude, latitude)
        params: wind-field parameters
        land_mask: callable returning True for land at (lon, lat)
        thresholds_ms: wind thresholds (m/s) for duration accounting.
            Empty result if None or empty.

    Returns:
        WindFieldOutput summarising the time series and peak metadata.
    """
    states = trajectory.states
    if not states:
        return WindFieldOutput(
            point_id=property_point.property_id,
            longitude=property_point.longitude,
            latitude=property_point.latitude,
            time_hours=[],
            sustained_ms=[],
            peak_sustained_ms=0.0,
            time_of_peak_hours=0.0,
            distance_at_peak_km=0.0,
            azimuth_at_peak_deg=0.0,
            duration_above_ms={},
        )

    time_hours: List[float] = []
    sustained_ms: List[float] = []
    distance_km_series: List[float] = []
    azimuth_deg_series: List[float] = []

    for state in states:
        result = evaluate_point_with_geometry(
            state=state,
            point_lon=property_point.longitude,
            point_lat=property_point.latitude,
            params=params,
            land_mask=land_mask,
        )
        time_hours.append(state.time_hours)
        sustained_ms.append(result.sustained_ms)
        distance_km_series.append(result.distance_km)
        azimuth_deg_series.append(result.azimuth_deg)

    peak_idx = max(range(len(sustained_ms)), key=lambda i: sustained_ms[i])

    duration_above_ms = {}
    if thresholds_ms is not None:
        for threshold in thresholds_ms:
            duration_above_ms[float(threshold)] = duration_above_threshold(
                time_hours, sustained_ms, float(threshold),
            )

    return WindFieldOutput(
        point_id=property_point.property_id,
        longitude=property_point.longitude,
        latitude=property_point.latitude,
        time_hours=time_hours,
        sustained_ms=sustained_ms,
        peak_sustained_ms=sustained_ms[peak_idx],
        time_of_peak_hours=time_hours[peak_idx],
        distance_at_peak_km=distance_km_series[peak_idx],
        azimuth_at_peak_deg=azimuth_deg_series[peak_idx],
        duration_above_ms=duration_above_ms,
    )
