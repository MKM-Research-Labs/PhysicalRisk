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
"""SP-001's formulae, from its model document (``spatial_model.pdf`` v1.0, s3), at 50 digits.

Written from the document, not the code: the haversine of Eq. 2 in its arctangent form
on a sphere of 6,371,000 m; the IDW of Eq. 1 with the haversine distance, power p and
s3.1's threshold (the first gauge closer than it returns its own value); the WSE at a
gauge as its depth plus its elevation (s4.1); the correlation of Eq. 3 with d the
haversine distance; the nearest gauge by that distance (s3.3, s4.2); and the true
nearest point on a segment drawn straight in latitude and longitude, found by
minimising the haversine distance along it -- what the flat-Earth projection of s5.2(3)
approximates.
"""

import mpmath as mp

from config.models import ORACLE_SP_DEG_KM, ORACLE_SP_EARTH_R_M, ORACLE_SP_MIN_DISTANCE_M, ORACLE_SP_POWER


def _m(x):
    return mp.mpf(x)


def haversine(lat1, lon1, lat2, lon2):
    """Eq. 2, in metres."""
    p1, p2 = mp.radians(_m(lat1)), mp.radians(_m(lat2))
    dp, dl = mp.radians(_m(lat2) - _m(lat1)), mp.radians(_m(lon2) - _m(lon1))
    a = mp.sin(dp / 2) ** 2 + mp.cos(p1) * mp.cos(p2) * mp.sin(dl / 2) ** 2
    return 2 * ORACLE_SP_EARTH_R_M * mp.atan2(mp.sqrt(a), mp.sqrt(1 - a))


def idw(pairs, p=ORACLE_SP_POWER, d_min=ORACLE_SP_MIN_DISTANCE_M):
    """Eq. 1 over (distance m, value) pairs; the first gauge within d_min returns its value."""
    num = den = mp.mpf(0)
    for d, z in pairs:
        d, z = _m(d), _m(z)
        if d < _m(d_min):
            return z
        w = 1 / d ** _m(p)
        num, den = num + w * z, den + w
    return num / den


def wse(target, gauges, p=ORACLE_SP_POWER, d_min=ORACLE_SP_MIN_DISTANCE_M):
    """s3.1 at a target (lat, lon) from gauges (lat, lon, elevation, depth)."""
    return idw([(haversine(*target, lat, lon), _m(el) + _m(dep)) for lat, lon, el, dep in gauges], p, d_min)


def correlation(points, length_m, rho0):
    """Eq. 3 with d the haversine distance: {(i, j): rho_ij} for i < j."""
    return {(i, j): _m(rho0) * mp.exp(-haversine(*points[i], *points[j]) / _m(length_m))
            for i in range(len(points)) for j in range(i + 1, len(points))}


def correlation_degrees(points, length_m, rho0):
    """The code's convention (DD-001 v2.0, Eq. 9): Euclidean degrees at 111 km a degree."""
    out = {}
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = mp.sqrt((_m(points[i][0]) - _m(points[j][0])) ** 2 + (_m(points[i][1]) - _m(points[j][1])) ** 2)
            out[(i, j)] = _m(rho0) * mp.exp(-d * ORACLE_SP_DEG_KM / (_m(length_m) / 1000))
    return out


def nearest(target, gauges):
    """s3.3, s4.2: the index of the nearest gauge (lat, lon) by Eq. 2."""
    d = [haversine(*target, *g) for g in gauges]
    return d.index(min(d))


def on_segment(p, a, b):
    """The nearest point to p on the segment a-b drawn straight in (lat, lon): (distance m, t)."""
    f = lambda t: haversine(*p, _m(a[0]) + t * (_m(b[0]) - _m(a[0])), _m(a[1]) + t * (_m(b[1]) - _m(a[1])))  # noqa: E731
    lo, hi, g = mp.mpf(0), mp.mpf(1), (mp.sqrt(5) - 1) / 2
    for _ in range(160):
        c, d = hi - g * (hi - lo), lo + g * (hi - lo)
        lo, hi = (lo, d) if f(c) < f(d) else (c, hi)
    t = (lo + hi) / 2
    return min((f(t), t), (f(mp.mpf(0)), mp.mpf(0)), (f(mp.mpf(1)), mp.mpf(1)))


def on_polyline(p, poly):
    """The nearest point on a polyline: (distance m, segment index, t)."""
    best = min((on_segment(p, poly[i], poly[i + 1]) + (i,) for i in range(len(poly) - 1)), key=lambda r: r[0])
    return best[0], best[2], best[1]
