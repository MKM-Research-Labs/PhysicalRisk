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

"""Coordinate geometry for the wind-field model — spec eqs. (20) and (21).

Defines the radial distance r(x, t) and azimuth theta(x, t) from a storm
center c_t = (lon_c, lat_c) to an evaluation point x = (lon_x, lat_x).
Uses the standard great-circle Haversine formula for distance and the
forward-azimuth formula for bearing.

Conventions used elsewhere in the typhoon model are preserved:
- Latitude / longitude in degrees, WGS-84-style.
- Bearing in compass degrees (0 = North, increasing clockwise).
"""

import math

from models.typhoon.transitions.position import EARTH_RADIUS_KM


__all__ = [
    "haversine_distance_km",
    "bearing_deg",
]


def haversine_distance_km(
    lon_c: float,
    lat_c: float,
    lon_x: float,
    lat_x: float,
) -> float:
    """Great-circle distance between center and evaluation point, in km.

    Standard Haversine — accurate at all latitudes, robust against
    floating-point cancellation near antipodes.
    """
    lat_c_rad = math.radians(lat_c)
    lat_x_rad = math.radians(lat_x)
    dlat = math.radians(lat_x - lat_c)
    dlon = math.radians(lon_x - lon_c)

    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat_c_rad) * math.cos(lat_x_rad) * math.sin(dlon / 2.0) ** 2
    )
    # atan2 form is numerically stable for very small a (very close points).
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def bearing_deg(
    lon_c: float,
    lat_c: float,
    lon_x: float,
    lat_x: float,
) -> float:
    """Compass bearing from the center toward the evaluation point.

    Returns degrees in [0, 360). 0 = due north, 90 = due east, etc.
    Undefined for coincident points; callers must guard r > 0 if the
    bearing matters there.
    """
    lat_c_rad = math.radians(lat_c)
    lat_x_rad = math.radians(lat_x)
    dlon = math.radians(lon_x - lon_c)

    y = math.sin(dlon) * math.cos(lat_x_rad)
    x = (
        math.cos(lat_c_rad) * math.sin(lat_x_rad)
        - math.sin(lat_c_rad) * math.cos(lat_x_rad) * math.cos(dlon)
    )
    theta_rad = math.atan2(y, x)
    return math.degrees(theta_rad) % 360.0
