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
"""DD-001's filed document, tested as stated (``flood_risk.pdf`` v1.1).

Tables 5-7 are judged as printed: the code, rounded as the generator rounded it,
must give each printed figure. Table 9's velocities, Table 8's curve-shift ratios
and s8's distance error are recomputed from the document's own equations. The
code's undocumented degree-5 curve is judged against the fit its config states.
"""

import inspect
import math
import subprocess

import mpmath as mp
import numpy as np

from config import config
from config.damage import DD_POLY_COEFFS
from config.models import (
    ORACLE_DD_CLAIM_DEG_ERR,
    ORACLE_DD_CLAIM_MEMORY,
    ORACLE_DD_DOC_ATTENUATION_M,
    ORACLE_DD_LATITUDE,
    ORACLE_DD_PORTFOLIO_N,
    ORACLE_DD_PRINTED_S334,
    ORACLE_DD_PRINTED_T5,
    ORACLE_DD_PRINTED_T6,
    ORACLE_DD_PRINTED_T7,
    ORACLE_DD_PRINTED_T8,
    ORACLE_DD_PRINTED_T9,
    ORACLE_DD_PRINTED_T10,
    ORACLE_DD_ROUND,
    ORACLE_DD_TABLE5_DEPTHS,
    ORACLE_DD_TABLE6,
    ORACLE_DD_TABLE7,
    ORACLE_DD_TABLE9,
    ORACLE_DD_TABLE10,
)
from tools.wolfram_oracle.depthdamage import reference as ref

# The fit DD_POLY_COEFFS's comment states (config/damage.py).
POLY_STATED = {"r2": 0.999244, "rmse": 0.009368, "max_err": 0.020388, "f6": 1.001}


def printed(v, places):
    """A value as the generator printed it: rounded, then formatted by size."""
    v = round(float(v), places)
    return f"{v:.2f}" if abs(v) >= 1 else f"{v:.4f}"


def _tables(m):
    vel, dmg = m["velocity"], m["damage"]
    t6 = ORACLE_DD_TABLE6
    got5 = [printed(dmg.scalar_depth_damage(d), ORACLE_DD_ROUND["t5"]) for d in ORACLE_DD_TABLE5_DEPTHS]
    got6 = [[printed(vel.compute_manning_velocity(h, t6["slope"], n), ORACLE_DD_ROUND["t6"]) for h in t6["depths"]]
            for n in t6["n"]]
    got7 = [[printed(vel.compute_retention(d, length=ell), ORACLE_DD_ROUND["t7"]) for ell in ORACLE_DD_TABLE7["lengths"]]
            for d in ORACLE_DD_TABLE7["distances"]]
    flat = lambda t: [c for row in t for c in row]
    return {k: (sum(a == b for a, b in zip(g, p)), len(p)) for k, g, p in (
        ("t5", got5, ORACLE_DD_PRINTED_T5), ("t6", flat(got6), flat(ORACLE_DD_PRINTED_T6)),
        ("t7", flat(got7), flat(ORACLE_DD_PRINTED_T7)))}


def poly_fit():
    """The stated fit of DD_POLY_COEFFS to Table 1, recomputed."""
    xs = [d for d, _ in ref.table1()]
    ys = [v for _, v in ref.table1()]
    f = lambda h: mp.fsum(mp.mpf(c) * h ** (i + 1) for i, c in enumerate(DD_POLY_COEFFS))
    res = [f(x) - y for x, y in zip(xs, ys)]
    mean = mp.fsum(ys) / len(ys)
    slope_min = min(mp.diff(f, mp.mpf(i) / 100) for i in range(601))
    return {"r2": 1 - mp.fsum(r * r for r in res) / mp.fsum((y - mean) ** 2 for y in ys),
            "rmse": mp.sqrt(mp.fsum(r * r for r in res) / len(res)),
            "max_err": max(abs(r) for r in res), "f6": f(mp.mpf(6)), "slope_min": slope_min}


def _unused(name):
    """Whether a config constant is read anywhere in src/."""
    out = subprocess.run(["git", "grep", "-l", name, "--", "src"], capture_output=True, text=True,
                         cwd=config.get_project_root())
    return not out.stdout.strip()


def assess(m, mc, up, down, hydro_gap, min_eig):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    t = _tables(m)
    t9 = ORACLE_DD_TABLE9
    v9 = [float(ref.manning(t9["depth"], t9["slope"], n)) for n in t9["n"]]
    implied = [v * h * 3600 for v, h in zip(ORACLE_DD_PRINTED_T9["velocity"], ORACLE_DD_PRINTED_T9["travel"])]
    t10 = [math.exp(-ORACLE_DD_TABLE10["distance"] / ell) for ell in ORACLE_DD_TABLE10["lengths"]]
    el = (up["exact"] / mc["exact"], down["exact"] / mc["exact"])
    single = [float(ref.expected_clipped(1.1 * d) / ref.expected_clipped(d)) for d in (0.3, 0.6, 0.9)]
    deg_err = 1 / math.cos(math.radians(ORACLE_DD_LATITUDE)) - 1
    n_mem, mem = ORACLE_DD_CLAIM_MEMORY
    poly = poly_fit()
    ell_code = float(inspect.signature(m["velocity"].compute_retention).parameters["length"].default)
    return {
        "t5": {**_counts(t["t5"])}, "t6": {**_counts(t["t6"])}, "t7": {**_counts(t["t7"])},
        "s334": {"met": [round(math.exp(-1), 2), round(math.exp(-3), 2)] == list(ORACLE_DD_PRINTED_S334)},
        "t10": {"values": t10, "met": [round(x, 2) for x in t10] == list(ORACLE_DD_PRINTED_T10)},
        "t9": {"eq11": v9, "implied_m": implied, "met": False},
        "t8": {"el": el, "var99": up["var99"] / mc["var99"] - 1, "es99": up["es99"] / mc["es99"] - 1,
               "single": single, "met": abs(el[0] - ORACLE_DD_PRINTED_T8["el"][0]) < 0.005},
        "s8": {"error": deg_err, "met": abs(deg_err - ORACLE_DD_CLAIM_DEG_ERR) < 0.01},
        "ell": {"code": ell_code, "doc": ORACLE_DD_DOC_ATTENUATION_M, "met": ell_code == ORACLE_DD_DOC_ATTENUATION_M},
        "eq2": {"unused": [k for k in ("PROPERTY_TYPE_DAMAGE_FACTORS", "FLOOD_MAX_DISTANCE_M") if _unused(k)],
                "met": None},
        "eq15": {"depth_gap": hydro_gap, "met": None},
        "psd": {"min_eig": min_eig, "met": min_eig > 0},
        "memory": {"bytes": n_mem ** 2 * 8, "met": n_mem ** 2 * 8 == mem},
        "hhi": {"value": float(m["risk"].calculate_hhi(np.ones(ORACLE_DD_PORTFOLIO_N))),
                "met": abs(m["risk"].calculate_hhi(np.ones(ORACLE_DD_PORTFOLIO_N)) - 1 / ORACLE_DD_PORTFOLIO_N) < 1e-15},
        # np.random.multivariate_normal (RandomState) factorises by SVD, not Cholesky
        "cholesky": {"method": "svd", "met": None},
        "poly": {**{k: float(v) for k, v in poly.items()},
                 "met": all(abs(float(poly[k]) - v) <= 0.5 * 10 ** -p for k, v, p in
                            (("r2", POLY_STATED["r2"], 6), ("rmse", POLY_STATED["rmse"], 6),
                             ("max_err", POLY_STATED["max_err"], 6), ("f6", POLY_STATED["f6"], 3)))
                 and poly["slope_min"] > 0},
    }


def _counts(c):
    return {"matched": c[0], "of": c[1], "met": c[0] == c[1]}
