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
"""DD-001's formulae, from its filed document (``flood_risk.pdf`` v1.1, s3), at 50 digits.

Written from the document, not the code: Eq. 1's curve from Table 1, Manning (Eqs.
11-13), the attenuation of Eq. 14, the property hydrograph of Eqs. 15-17, the
haversine of Eq. 7, IDW (Eq. 8), the correlation of Eq. 10, and the exact expected
loss under Eq. 18's clipped shock -- the shocked ratio delta (1 + 0.2 z) is normal,
so its clipped mean is a truncated-normal integral.
"""

import mpmath as mp

from config.damage import DAMAGE_POINTS, DEPTH_POINTS
from config.models import ORACLE_DD_DEG_KM, ORACLE_DD_EARTH_R_M, ORACLE_DD_SHOCK

# Table 1 as printed, and S_min: strings, made numbers at the working precision
# when used (an mpf built at import would carry only the default 53 bits).
TABLE1_TEXT = (("0", "0"), ("0.05", "0.05"), ("0.5", "0.25"), ("1.0", "0.40"), ("1.5", "0.50"),
               ("2.0", "0.60"), ("3.0", "0.75"), ("4.0", "0.85"), ("5.0", "0.95"), ("6.0", "1.0"))
MIN_SLOPE_TEXT = "0.001"


def table1():
    return [(mp.mpf(d), mp.mpf(v)) for d, v in TABLE1_TEXT]


def table1_matches_config():
    return [float(d) for d, _ in TABLE1_TEXT] == list(map(float, DEPTH_POINTS)) and \
        [float(v) for _, v in TABLE1_TEXT] == list(map(float, DAMAGE_POINTS))


def damage(d):
    """Eq. 1, with delta = 0 at or below 0 and 1 at or above 6 m."""
    d, pts = mp.mpf(d), table1()
    if d <= 0:
        return mp.mpf(0)
    if d >= pts[-1][0]:
        return mp.mpf(1)
    for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
        if d0 <= d < d1:
            return v0 + (v1 - v0) * (d - d0) / (d1 - d0)


def slope_clamped(s):
    return max(abs(mp.mpf(s)), mp.mpf(MIN_SLOPE_TEXT))


def manning(h, s, n):
    """Eq. 11, with the slope clamped at S_min (s3.3.1) and zero for h <= 0 or n <= 0."""
    h, n = mp.mpf(h), mp.mpf(n)
    if h <= 0 or n <= 0:
        return mp.mpf(0)
    return h ** (mp.mpf(2) / 3) * mp.sqrt(slope_clamped(s)) / n


def travel_hours(d, h, s, n):
    """Eq. 13."""
    v = manning(h, s, n)
    return mp.inf if v == 0 else mp.mpf(d) / (v * 3600)


def slope(e_gauge, e_prop, d):
    """Eq. 12."""
    floor = mp.mpf(MIN_SLOPE_TEXT)
    return floor if d <= 0 else max(abs(mp.mpf(e_gauge) - mp.mpf(e_prop)) / mp.mpf(d), floor)


def attenuation(d, ell):
    """Eq. 14."""
    return mp.exp(-mp.mpf(d) / mp.mpf(ell))


def haversine(lat1, lon1, lat2, lon2):
    """Eq. 7, in its arcsine form."""
    p1, l1, p2, l2 = (mp.radians(mp.mpf(x)) for x in (lat1, lon1, lat2, lon2))
    a = mp.sin((p2 - p1) / 2) ** 2 + mp.cos(p1) * mp.cos(p2) * mp.sin((l2 - l1) / 2) ** 2
    return 2 * ORACLE_DD_EARTH_R_M * mp.asin(mp.sqrt(a))


def idw(pairs, p=2, d_min=1):
    """Eq. 8: the first gauge within d_min returns its WSE directly."""
    for d, w in pairs:
        if mp.mpf(d) < d_min:
            return mp.mpf(w)
    wts = [1 / mp.mpf(d) ** p for d, _ in pairs]
    return mp.fsum(wt * mp.mpf(w) for wt, (_, w) in zip(wts, pairs)) / mp.fsum(wts)


def correlation(coords, ell_m, rho0):
    """Eq. 10: distances in degrees, times 111 km, unit diagonal."""
    n = len(coords)
    out = mp.matrix(n, n)
    for i in range(n):
        for j in range(n):
            if i == j:
                out[i, j] = 1
            else:
                dd = mp.sqrt(sum((mp.mpf(a) - mp.mpf(b)) ** 2 for a, b in zip(coords[i], coords[j])))
                out[i, j] = rho0 * mp.exp(-dd * ORACLE_DD_DEG_KM / (mp.mpf(ell_m) / 1000))
    return out


def hydrograph(levels, peak_wse, travel, a, e_prop, floor, gamma):
    """Eqs. 15-17, hour by hour, sampling the gauge at the nearest hour."""
    base, peak = min(levels), max(levels)
    i_peak, n, out = levels.index(peak), len(levels), []
    for t in range(n):
        src = t - travel
        if src < 0:
            out.append((mp.mpf(base), mp.mpf(0)))
            continue
        if t <= i_peak + travel:
            k = int(round(src))
        else:
            k = int(round(i_peak + (t - (i_peak + travel)) / gamma))
        k = max(0, min(k, n - 1))
        s = (mp.mpf(levels[k]) - base) / (peak - base)
        w = base + (mp.mpf(peak_wse) - base) * s * a
        out.append((w, max(mp.mpf(0), w - e_prop - floor)))
    return out


def expected_clipped(delta, shock=ORACLE_DD_SHOCK):
    """E[clip(delta (1 + shock Z), 0, 1)], Z standard normal (Eq. 18)."""
    mu = mp.mpf(delta)
    if mu == 0:
        return mp.mpf(0)
    s = mp.mpf(str(shock)) * mu                            # the document's 0.2, exactly
    lo, hi = -mu / s, (1 - mu) / s
    inside = mu * (mp.ncdf(hi) - mp.ncdf(lo)) + s * (mp.npdf(lo) - mp.npdf(hi))
    return inside + mp.ncdf(-hi)

