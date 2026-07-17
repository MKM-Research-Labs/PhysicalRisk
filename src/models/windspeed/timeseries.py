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

"""Convenience helpers for building a wind-speed timeseries at one point
across many hours within an event.

Note: the port pipeline already pre-computes per-property wind timeseries
to disk (see src/models/typhoon/pipeline/). This module is for ad-hoc
queries (e.g. a point not in the configured property portfolio, or a
finer time grid than dt_hours).
"""

from pathlib import Path
from typing import Iterable, List, Union

from config.typhoon import LandMask, WindFieldParams
from models.typhoon.data_structures import TyphoonTrajectory
from models.typhoon.wind_field import evaluate_point
from models.windspeed.interpolation import interpolate_state_at_hour
from models.windspeed.loader import load_event


__all__ = ["windspeed_series"]


def windspeed_series(
    event: Union[Path, str, TyphoonTrajectory],
    hours: Iterable[float],
    lon: float,
    lat: float,
    *,
    wind_field_params: WindFieldParams,
    land_mask: LandMask,
) -> List[float]:
    """Return sustained wind speed (m/s) at (lon, lat) at each hour in `hours`.

    Args:
        event: a path to an EVT-*.json file, or an already-loaded trajectory
        hours: iterable of hours since the event's genesis
        lon: longitude of the query point (degrees east)
        lat: latitude of the query point (degrees north)
        wind_field_params: wind-field calibration (from CatchmentTyphoonConfig)
        land_mask: callable (lon, lat) -> True if land at that point

    Returns:
        list of sustained wind speeds (m/s), one per requested hour
    """
    trajectory = load_event(event)
    return [
        evaluate_point(
            interpolate_state_at_hour(trajectory.states, h),
            lon, lat,
            wind_field_params,
            land_mask,
        )
        for h in hours
    ]
