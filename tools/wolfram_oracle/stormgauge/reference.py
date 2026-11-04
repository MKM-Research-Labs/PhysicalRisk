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
"""SG-001's formulae, from its model document (``storm_gauge_v2.0.pdf``, s3), at 50 digits.

Written from the document, not the code: the haversine of Eqs. 1-2 in its arctangent
form, the track interpolation of Eqs. 3-6 (at the first point before it, the last
after it, nothing after the storm's duration), the kernels of Eqs. 7-10, the intensity
at the gauge (Eq. 11), the power law of Eqs. 12-13, the lagged response of Eqs. 14-16
with its own rise and fall constants on s3.6's grid -- the storm's duration and five
fall constants more -- and the statistics of s3.7 (Eqs. 17-18).
"""

import mpmath as mp

from config.models import ORACLE_SG_EARTH_R_KM, ORACLE_SG_GAMMA, ORACLE_SG_RECESSION

KERNELS = ("gaussian", "exponential", "linear")


def _m(x):
    return mp.mpf(x)


def haversine(lon1, lat1, lon2, lat2):
    """Eqs. 1-2, in km."""
    p1, p2 = mp.radians(_m(lat1)), mp.radians(_m(lat2))
    dp, dl = mp.radians(_m(lat2) - _m(lat1)), mp.radians(_m(lon2) - _m(lon1))
    a = mp.sin(dp / 2) ** 2 + mp.cos(p1) * mp.cos(p2) * mp.sin(dl / 2) ** 2
    return 2 * ORACLE_SG_EARTH_R_KM * mp.atan2(mp.sqrt(a), mp.sqrt(1 - a))


def kernel(d, footprint, kind, param):
    """Eqs. 7-10; k = 1 on the track (s3.3's boundary condition)."""
    d = _m(d)
    if d <= 0:
        return mp.mpf(1)
    x, p = d / _m(footprint), _m(param)
    if kind == "gaussian":
        return mp.exp(-x ** 2 / (2 * p ** 2))
    if kind == "exponential":
        return mp.exp(-x / p)
    return max(mp.mpf(0), 1 - x / p)


def position(track, t):
    """Eqs. 3-6: (lon, lat, intensity) at time t; track = [(lon, lat, t, I), ...]."""
    t = _m(t)
    pts = [tuple(_m(v) for v in p) for p in track]
    if t <= pts[0][2]:
        return pts[0][0], pts[0][1], pts[0][3]
    if t >= pts[-1][2]:
        return pts[-1][0], pts[-1][1], pts[-1][3]
    for p, q in zip(pts, pts[1:]):
        if p[2] <= t < q[2]:
            a = min(mp.mpf(1), max(mp.mpf(0), (t - p[2]) / (q[2] - p[2])))
            return tuple(p[k] + a * (q[k] - p[k]) for k in (0, 1, 3))


def intensity_at(track, t, glon, glat, footprint, kind, param, duration):
    """Eq. 11; zero after the storm's duration (s3.2)."""
    if _m(t) > _m(duration):
        return mp.mpf(0)
    lon, lat, i = position(track, t)
    return i * kernel(haversine(glon, glat, lon, lat), footprint, kind, param)


def high(gauge):
    """s3.5: the historical high, or 1.1 x the severe level without one."""
    h = gauge.get("historical_high")
    return _m(h) if h is not None else mp.mpf("1.1") * _m(gauge["severe_warning"])


def contribution(i, gauge, gamma=ORACLE_SG_GAMMA):
    """Eqs. 12-13; zero for I <= 0."""
    i = _m(i)
    if i <= 0:
        return mp.mpf(0)
    rng = high(gauge) - _m(gauge["base_level"])
    return (i / 100) ** mp.mpf(gamma) * rng * _m(gauge.get("sensitivity", 1.0))


def response(track, duration, gauge, footprint, kind, param, dt, lag, rise, decay):
    """Eqs. 14-18 on s3.6's grid t_i = i dt, i = 0..floor((T + 5 tau_decay)/dt)."""
    dt, lag, rise, decay = _m(dt), _m(lag), _m(rise), _m(decay)
    n = int(mp.floor((_m(duration) + ORACLE_SG_RECESSION * decay) / dt)) + 1
    times = [i * dt for i in range(n)]
    ints = [intensity_at(track, t, gauge["longitude"], gauge["latitude"], footprint, kind, param, duration)
            for t in times]
    k = int(mp.floor(lag / dt))
    up, down = min(mp.mpf(1), dt / rise), min(mp.mpf(1), dt / decay)
    c, levels = mp.mpf(0), []
    for i in range(n):
        target = contribution(ints[max(0, i - k)], gauge)
        c += (target - c) * (up if target > c else down)
        levels.append(_m(gauge["base_level"]) + c)
    return times, ints, levels


def statistics(times, ints, levels, gauge, dt):
    """s3.7: peaks and their times, durations above each stage (Eq. 17), accumulation (Eq. 18)."""
    dt, alert = _m(dt), _m(gauge["flood_alert"])
    pk = max(levels)
    pi = max(ints)
    out = {"peak_level": pk, "peak_time": times[levels.index(pk)],
           "peak_intensity": pi, "peak_intensity_time": times[ints.index(pi)],
           "accumulation": mp.fsum(max(mp.mpf(0), lv - alert) * dt for lv in levels)}
    for key, stage in (("alert", "flood_alert"), ("warning", "flood_warning"), ("severe", "severe_warning")):
        out[f"duration_{key}"] = dt * sum(1 for lv in levels if lv >= _m(gauge[stage]))
    return out
