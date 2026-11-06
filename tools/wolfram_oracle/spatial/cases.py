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

"""SP-001's code against its document, case by case.

Each family calls the production function and the 50-digit reference with the same
inputs; the largest relative error (metres for distances) is the family's result. The
correlation is Eq. 3 as v2.0 states it: Euclidean degrees at 111 km a degree. The spatial index and the projection are judged
by what they return: the gauge the index calls nearest and its distance, and the
distance to the point the projection finds.
"""

import importlib
import math

import mpmath as mp
import numpy as np

from config.models import (
    ORACLE_SP_CORR,
    ORACLE_SP_CORR_POINTS,
    ORACLE_SP_FLAT_EARTH_KM,
    ORACLE_SP_GAUGES,
    ORACLE_SP_IDW,
    ORACLE_SP_MODULE,
    ORACLE_SP_OFFSETS_KM,
    ORACLE_SP_POLYLINE,
    ORACLE_SP_POWERS,
    ORACLE_SP_SEGMENTS,
    ORACLE_SP_TARGET,
    ORACLE_SP_TREE_CASE,
    ORACLE_SP_TREE_RANDOM,
    ORACLE_SP_UK_PAIRS,
)
from tools.wolfram_oracle._wl import rel_err
from tools.wolfram_oracle.spatial import reference as ref

# (lat1, lon1, lat2, lon2): the UK pairs, a metre apart, the same point, one degree, across the dateline.
POINTS = ORACLE_SP_UK_PAIRS + ((51.5, -0.1, 51.50001, -0.1), (51.5, -0.1, 51.5, -0.1),
                               (51.4, -1.0, 52.4, -1.0), (51.5, 179.9, 51.5, -179.9))
KM_PER_DEG = 111.195
DIRECTIONS = {"north": (1.0, 0.0), "east": (0.0, 1.0), "north-west": (math.sqrt(0.5), -math.sqrt(0.5))}


def load():
    return importlib.import_module(ORACLE_SP_MODULE)


def _worst(pairs):
    return max(rel_err(a, b) for a, b in pairs)


def wse_cases():
    """(target, gauges): the configured target, one on a gauge, one 0.5 m from it, one far off."""
    g = ORACLE_SP_GAUGES
    return [(ORACLE_SP_TARGET, g), ((g[0][0], g[0][1]), g), ((g[1][0] + 4.5e-6, g[1][1]), g),
            ((51.9, -0.6), g), (ORACLE_SP_TARGET, g[:1])]


def _wse_code(sp, target, gauges):
    depth = {f"G{i}": dep for i, (_, _, _, dep) in enumerate(gauges)}
    meta = {f"G{i}": {"latitude": la, "longitude": lo, "elevation": el} for i, (la, lo, el, _) in enumerate(gauges)}
    return sp.spatial_interpolate_wse(target[0], target[1], depth, meta)


def correlation_code(sp, points=ORACLE_SP_CORR_POINTS):
    import geopandas as gpd
    from shapely.geometry import Point
    gdf = gpd.GeoDataFrame(geometry=[Point(lon, lat) for lat, lon in points])
    return sp.build_correlation_matrix(gdf, ORACLE_SP_CORR["length_m"], ORACLE_SP_CORR["base"])


def offset(mid, km, direction):
    fy, fx = DIRECTIONS[direction]
    dlat = km / KM_PER_DEG
    return mid[0] + dlat * fy, mid[1] + dlat * fx / math.cos(math.radians(mid[0]))


def projections(sp):
    """Every (segment, offset, direction): (offset km, code distance, true distance, code t, true t)."""
    out = []
    for a, b in ORACLE_SP_SEGMENTS:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        for km in ORACLE_SP_OFFSETS_KM:
            for direction in DIRECTIONS:
                p = offset(mid, km, direction)
                _, _, d, t = sp.nearest_point_on_segment(p[0], p[1], a[0], a[1], b[0], b[1])
                true_d, true_t = ref.on_segment(p, a, b)
                out.append((km, d, true_d, t, true_t))
    return out


def _proj_err(d, true_d):
    """Relative error of the distance; metres where the point is on the segment."""
    return float(abs(mp.mpf(d) - true_d) / true_d) if true_d > 1 else float(abs(mp.mpf(d) - true_d))


def projection(sp):
    rows = projections(sp)
    near = [r for r in rows if r[0] <= ORACLE_SP_FLAT_EARTH_KM]
    far = [r for r in rows if r[0] > ORACLE_SP_FLAT_EARTH_KM]
    poly = [(lat, lon) for lat, lon in (offset((51.5, -0.18), km, dn) for km in (0.05, 0.5, 3) for dn in DIRECTIONS)]
    seg_off = 0
    for p in poly:
        got = sp.nearest_point_on_polyline(p[0], p[1], list(ORACLE_SP_POLYLINE))
        want = ref.on_polyline(p, ORACLE_SP_POLYLINE)
        seg_off += got[3] != want[1]
    return {"table4": table4(rows), "near": max(_proj_err(d, td) for _, d, td, _, _ in near),
            "far": max(_proj_err(d, td) for _, d, td, _, _ in far),
            "far_m": max(float(abs(mp.mpf(d) - td)) for _, d, td, _, _ in far),
            "t": max(float(abs(mp.mpf(t) - tt)) for *_, t, tt in near),
            "polyline_segments_off": seg_off, "polyline_points": len(poly), "cases": len(rows)}


def _tree_pick(sp, target, gauges):
    """The index's answer: (row, distance m)."""
    import pandas as pd
    tree = sp.build_spatial_index(pd.DataFrame({"latitude": [g[0] for g in gauges],
                                                "longitude": [g[1] for g in gauges]}))
    return sp.nearest_gauge(tree, *target)


def tree(sp):
    """s3.3: the gauge the index calls nearest, and its distance, against Eq. 1's."""
    c = ORACLE_SP_TREE_CASE
    dist = [float(ref.haversine(*c["target"], *g)) for g in c["gauges"]]
    case = {"picked": _tree_pick(sp, c["target"], c["gauges"])[0], "nearest": ref.nearest(c["target"], c["gauges"]),
            "distances_m": dist}
    r = ORACLE_SP_TREE_RANDOM
    rng = np.random.default_rng(r["seed"])
    wrong = total = 0
    dist_err = 0.0
    for _ in range(r["networks"]):
        gauges = [tuple(x) for x in np.column_stack([rng.uniform(*r["lat"], r["gauges"]), rng.uniform(*r["lon"], r["gauges"])])]
        for q in np.column_stack([rng.uniform(*r["lat"], r["queries"]), rng.uniform(*r["lon"], r["queries"])]):
            q = tuple(q)
            (got, d), want = _tree_pick(sp, q, gauges), ref.nearest(q, gauges)
            total += 1
            wrong += got != want
            dist_err = max(dist_err, rel_err(d, ref.haversine(*q, *gauges[want])))
    return {**case, "wrong": wrong, "queries": total, "distance_err": dist_err}


def table4(rows):
    """Table 5 as printed: the worst error at each offset, per cent (4 dp) and metres (3 dp)."""
    out = []
    for km in sorted({r[0] for r in rows}):
        at = [r for r in rows if r[0] == km]
        pct = max((_proj_err(d, td) for _, d, td, _, _ in at if td > 1), default=0.0)
        out.append((km, f"{100 * pct:.4f}", f"{max(float(abs(mp.mpf(d) - td)) for _, d, td, _, _ in at):.3f}"))
    return out


def deterministic(sp):
    """Each closed-form family's worst error, code against reference."""
    code = correlation_code(sp)
    deg = ref.correlation_degrees(ORACLE_SP_CORR_POINTS, ORACLE_SP_CORR["length_m"], ORACLE_SP_CORR["base"])
    return {
        "haversine_m": max(float(abs(mp.mpf(sp.haversine_distance(*p)) - ref.haversine(*p))) for p in POINTS),
        "idw": _worst((sp.idw_interpolate_from_gauges([(float(d), float(z)) for d, z in c], power=p), ref.idw(c, p))
                      for c in ORACLE_SP_IDW for p in ORACLE_SP_POWERS),
        "wse": _worst((_wse_code(sp, t, g), ref.wse(t, g)) for t, g in wse_cases()),
        "corr_degrees": _worst((code[i][j], v) for (i, j), v in deg.items()),
        "corr_diagonal": float(max(abs(code[i][i] - 1) for i in range(len(code)))),
    }
