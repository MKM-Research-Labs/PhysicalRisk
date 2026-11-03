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
"""DD-001's code against its document, case by case.

Each family of cases calls the production function and the 50-digit reference with
the same inputs; the largest relative error (absolute where the answer is zero) is
the family's result. The portfolio Monte Carlo is judged differently: its mean
against the exact expected loss, in standard errors of its own 1,000 draws.
"""

import importlib

import geopandas as gpd
import mpmath as mp
import numpy as np
from shapely.geometry import Point

from config.models import (
    ORACLE_DD_CORR,
    ORACLE_DD_MC_DRAWS,
    ORACLE_DD_MODULES,
    ORACLE_DD_PORTFOLIO_N,
    ORACLE_DD_PORTFOLIO_ORIGIN,
    ORACLE_DD_PORTFOLIO_STEP_DEG,
    ORACLE_DD_SLOPES,
    ORACLE_DD_TABLE5_DEPTHS,
    ORACLE_DD_TABLE6,
    ORACLE_DD_TABLE7,
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle._wl import rel_err
from tools.wolfram_oracle.depthdamage import reference as ref

GAUGE_HOURS = 168
POINTS = ((51.5, -0.1, 51.5, 0.0), (51.45, -0.3, 51.6, 0.15), (51.5, -0.1, 51.50001, -0.1),
          (51.4, -1.0, 52.4, -1.0), (50.0, -5.0, 55.0, 1.0), (51.5, 179.9, 51.5, -179.9))
IDW = (((500, 12.5), (2000, 11.8), (5000, 10.2)), ((100, 9.0), (100, 11.0)),
       ((0.5, 7.0), (2000, 11.8)), ((3000, 10.0),), ((750, 8.4), (1200, 9.9), (2500, 10.7), (9000, 12.0)))


def load():
    return {k: importlib.import_module(m) for k, m in ORACLE_DD_MODULES.items()}


def depths():
    return sorted(set(ORACLE_DD_TABLE5_DEPTHS) | {round(0.01 * i, 2) for i in range(-20, 701)})


def portfolio():
    """N properties on a grid, depths spanning every damage band, values 100k to 1.3m."""
    lat0, lon0 = ORACLE_DD_PORTFOLIO_ORIGIN
    rows = []
    for i in range(ORACLE_DD_PORTFOLIO_N):
        rows.append({"lat": lat0 + ORACLE_DD_PORTFOLIO_STEP_DEG * (i % 8),
                     "lon": lon0 + ORACLE_DD_PORTFOLIO_STEP_DEG * (i // 8),
                     "depth": round(0.15 * i, 2), "value": 100_000.0 + 30_000.0 * ((7 * i) % 41)})
    return rows


def _gdf(rows):
    return gpd.GeoDataFrame({"value": [r["value"] for r in rows]},
                            geometry=[Point(r["lon"], r["lat"]) for r in rows])


def gauge_series():
    """A triangular storm: base 2.0 m, peak 5.2 m at hour 40, slower recession."""
    out = []
    for h in range(GAUGE_HOURS):
        lvl = 2.0 + 3.2 * h / 40 if h <= 40 else max(2.0, 5.2 - 3.2 * (h - 40) / 70)
        out.append({"hour": h, "water_level_m": round(lvl, 4)})
    return out


def _worst(pairs):
    return max(rel_err(a, b) for a, b in pairs)


def deterministic(m):
    """Each family's worst error, code against reference."""
    dmg, vel, sp = m["damage"], m["velocity"], m["spatial"]
    t6 = ORACLE_DD_TABLE6
    grid = [(h, s, n) for n in t6["n"] + (0.0, -0.01) for h in t6["depths"] + (0.0, -0.3, 0.07)
            for s in ORACLE_DD_SLOPES]
    att = [(d, ell) for d in ORACLE_DD_TABLE7["distances"] + (-50, 17_500) for ell in ORACLE_DD_TABLE7["lengths"]]
    out = {
        "damage": _worst((dmg.scalar_depth_damage(d), ref.damage(d)) for d in depths()),
        "manning": _worst((vel.compute_manning_velocity(h, s, n), ref.manning(h, s, n)) for h, s, n in grid),
        "travel": _worst((vel.compute_travel_time(d, h, s, n), ref.travel_hours(d, h, s, n))
                         for d in (250, 2000, 3000) for h, s, n in grid if ref.manning(h, s, n) > 0),
        "slope": _worst((vel.compute_slope(g, p, d), ref.slope(g, p, d))
                        for g, p, d in ((12, 9.5, 800), (9.5, 12, 800), (10, 10, 500), (10, 9.99, 50_000), (5, 3, 0))),
        "attenuation": _worst((vel.compute_retention(d, ell), ref.attenuation(max(d, 0), ell)) for d, ell in att),
        # in metres: a 1 m separation loses relative digits to the inputs' own rounding
        "haversine_m": max(float(abs(sp.haversine_distance(*p) - ref.haversine(*p))) for p in POINTS),
        "idw": _worst((sp.idw_interpolate_from_gauges(list(c)), ref.idw(c)) for c in IDW),
    }
    out["travel_inf"] = vel.compute_travel_time(1000, 0.0, 0.005) == float("inf")
    return out


def correlation(m):
    rows = portfolio()[:10]
    got = m["spatial"].build_correlation_matrix(_gdf(rows), ORACLE_DD_CORR["distance_m"], ORACLE_DD_CORR["base"])
    want = ref.correlation([(r["lon"], r["lat"]) for r in rows], ORACLE_DD_CORR["distance_m"], ORACLE_DD_CORR["base"])
    err = max(rel_err(got[i, j], want[i, j]) for i in range(len(rows)) for j in range(len(rows)))
    return err, float(np.linalg.eigvalsh(got).min())


def hydrographs(m):
    """The code against Eqs. 15-17 without a (the code's reading) and with it (the document's)."""
    readings, levels = gauge_series(), [r["water_level_m"] for r in gauge_series()]
    worst, depth_gap = 0.0, 0.0
    for travel, a in ((0.0, 1.0), (2.4, 0.8), (7.0, 0.5)):
        got = m["velocity"].build_property_hydrograph(readings, 4.6, travel, a, 3.1, 0.3)
        plain = ref.hydrograph(levels, 4.6, travel, 1, 3.1, 0.3, 1.5)
        doc = ref.hydrograph(levels, 4.6, travel, a, 3.1, 0.3, 1.5)
        worst = max(worst, max(abs(g["wse_m"] - float(w)) + abs(g["depth_m"] - float(d))
                               for g, (w, d) in zip(got, plain)))
        depth_gap = max(depth_gap, float(max(d for _, d in plain) - max(d for _, d in doc)))
    return worst, depth_gap


def monte_carlo(m, shift=1.0):
    """The code's Monte Carlo on the portfolio against the exact expected loss."""
    rows = portfolio()
    gdf = _gdf(rows)
    corr = m["spatial"].build_correlation_matrix(gdf, ORACLE_DD_CORR["distance_m"], ORACLE_DD_CORR["base"])
    deltas = np.array([min(1.0, shift * m["damage"].scalar_depth_damage(r["depth"])) for r in rows])
    res = m["risk"].simulate_portfolio_impact(gdf, np.array([r["depth"] for r in rows]), deltas, corr,
                                              n_simulations=ORACLE_DD_MC_DRAWS)
    dist = res["impact_distribution"]
    with mp.workdps(ORACLE_REFERENCE_DPS):
        exact = mp.fsum(mp.mpf(r["value"]) * ref.expected_clipped(d) for r, d in zip(rows, deltas))
    se = dist.std(ddof=1) / np.sqrt(len(dist))
    q99 = np.percentile(dist, 99)
    return {"mean": float(res["mean_impact"]), "exact": float(exact), "se": float(se),
            "z": float((res["mean_impact"] - float(exact)) / se),
            "es99_err": rel_err(res["es_99"], dist[dist >= q99].mean()), "var99": float(res["var_99"]),
            "es99": float(res["es_99"]), "deltas": deltas, "values": [r["value"] for r in rows]}
