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
"""What Wolfram computes for SP-001, independently of the reference.

The great-circle distance as R times the angle between the two points' unit vectors
(not the haversine); Eq. 1 from exact inputs; Eq. 3 on that distance; the nearest point
on a segment where the squared chord along it is stationary (FindRoot); and the true distance between
the UK pairs on the WGS84 ellipsoid, by GeoDistance, for the document's claims that the
haversine is sufficient (s5.1(2)) and exact (Q2).
"""

import mpmath as mp

from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SP_CORR,
    ORACLE_SP_CORR_POINTS,
    ORACLE_SP_EARTH_R_M,
    ORACLE_SP_IDW,
    ORACLE_SP_SEGMENTS,
    ORACLE_SP_UK_PAIRS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_number, wl_precise
from tools.wolfram_oracle.spatial import cases
from tools.wolfram_oracle.spatial import reference as ref

_D = ORACLE_WOLFRAM_DIGITS


def _unit(lat, lon):
    p, l = (f"({x}) Pi/180" for x in (lat, lon))
    return f"{{Cos[{p}] Cos[{l}], Cos[{p}] Sin[{l}], Sin[{p}]}}"


def _angle(lat1, lon1, lat2, lon2):
    w = wl_precise
    return f"{ORACLE_SP_EARTH_R_M} VectorAngle[{_unit(w(lat1), w(lon1))}, {_unit(w(lat2), w(lon2))}]"


def _idw(pairs, p):
    w = wl_precise
    num = " + ".join(f"{w(z)}/{w(d)}^({p})" for d, z in pairs)
    den = " + ".join(f"1/{w(d)}^({p})" for d, _ in pairs)
    return f"N[({num})/({den}), {_D}]"


def _segment(p, a, b):
    """The least distance along the segment: the root of the squared chord's derivative
    between unit vectors (well conditioned, where minimising a flat function is not), then
    the arc 2R ArcSin[chord/2] there."""
    w = wl_precise
    lat = f"({w(a[0])} + t ({w(b[0])} - {w(a[0])}))"
    lon = f"({w(a[1])} + t ({w(b[1])} - {w(a[1])}))"
    q = f"Total[({_unit(w(p[0]), w(p[1]))} - {_unit(lat, lon)})^2]"
    # The cases below have their minimum inside the segment, so no endpoint check is needed.
    return (f"N[With[{{s = FindRoot[Evaluate[D[{q}, t] == 0], {{t, 1/2}}, WorkingPrecision -> 80, "
            f"PrecisionGoal -> 60, AccuracyGoal -> 60]}}, 2 {ORACLE_SP_EARTH_R_M} ArcSin[Sqrt[{q} /. s]/2]], {_D}]")


def segment_cases():
    """The diagonal segment, a point 1, 10 and 50 km north-west of its middle."""
    a, b = ORACLE_SP_SEGMENTS[2]
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return [(cases.offset(mid, km, "north-west"), a, b) for km in (1, 10, 50)]


def items(m=None):
    """(id, expression, reference) for every oracle; the reference is None where
    Wolfram's answer is itself the finding."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return _items()


def _items():
    out = [(f"sphere/{i}", f"N[{_angle(*p)}, {_D}]", ref.haversine(*p)) for i, p in enumerate(cases.POINTS)
           if p[:2] != p[2:]]
    for i, c in enumerate(ORACLE_SP_IDW):
        if all(d >= 1 for d, _ in c):
            for p, pw in (("2", 2), ("5/2", 2.5)):
                out.append((f"idw/{i}/{pw}", _idw(c, p), ref.idw(c, pw)))
    pts, L, r0 = ORACLE_SP_CORR_POINTS, ORACLE_SP_CORR["length_m"], ORACLE_SP_CORR["base"]
    doc = ref.correlation(pts, L, r0)
    for (i, j), v in doc.items():
        out.append((f"corr/{i}/{j}", f"N[{wl_precise(r0)} Exp[-{_angle(*pts[i], *pts[j])}/{wl_precise(L)}], {_D}]", v))
    for k, (p, a, b) in enumerate(segment_cases()):
        out.append((f"segment/{k}", _segment(p, a, b), ref.on_segment(p, a, b)[0]))
    for i, (a, b, c, d) in enumerate(ORACLE_SP_UK_PAIRS):
        out.append((f"wgs84/{i}", f"N[QuantityMagnitude[GeoDistance[GeoPosition[{{{wl_precise(a)}, {wl_precise(b)}}}], "
                                  f"GeoPosition[{{{wl_precise(c)}, {wl_precise(d)}}}]], \"Meters\"], {_D}]", None))
    return out


def judge(m, results):
    """Wolfram's worst disagreement with the reference, and the sphere's error against
    WGS84 for each UK pair (per cent)."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        its = _items()
        worst = max(rel_err(wl_number(results[i]), r) for i, _, r in its if r is not None)
        pct = [100 * float(ref.haversine(*p) / wl_number(results[f"wgs84/{i}"]) - 1)
               for i, p in enumerate(ORACLE_SP_UK_PAIRS)]
    return float(worst), pct
