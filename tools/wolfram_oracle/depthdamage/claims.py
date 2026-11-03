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
"""DD-001's model document, tested as stated (``flood_risk_v2.0.pdf``).

Tables 4-6 and 8 are judged as printed: the code, rounded as the generator rounds,
must give each printed figure. Table 7's curve-shift ratios are recomputed from the
exact expected loss, the retention quotes from Eq. 6, and the statements about what
the code does -- retention applied once, constants unread, SVD draws -- against the
code itself.
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
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle.depthdamage import reference as ref

# The fit the document (s3.1) and DD_POLY_COEFFS's comment state.
POLY_STATED = {"r2": 0.999244, "rmse": 0.009368, "max_err": 0.020388}
UNREAD = ("PROPERTY_TYPE_DAMAGE_FACTORS", "FLOOD_MAX_DISTANCE_M")


def printed(v, places):
    """A value as the generator printed it: rounded, then formatted by size."""
    v = round(float(v), places)
    return f"{v:.2f}" if abs(v) >= 1 else f"{v:.4f}"


def _matched(got, want):
    return {"matched": sum(a == b for a, b in zip(got, want)), "of": len(want)}


def tables(m):
    vel, dmg = m["velocity"], m["damage"]
    t6, t9 = ORACLE_DD_TABLE6, ORACLE_DD_TABLE9
    flat = lambda t: [c for row in t for c in row]
    out = {
        "t4": _matched([printed(dmg.scalar_depth_damage(d), ORACLE_DD_ROUND["t5"]) for d in ORACLE_DD_TABLE5_DEPTHS],
                       ORACLE_DD_PRINTED_T5),
        "t5": _matched([printed(vel.compute_manning_velocity(h, t6["slope"], n), ORACLE_DD_ROUND["t6"])
                        for n in t6["n"] for h in t6["depths"]], flat(ORACLE_DD_PRINTED_T6)),
        "t6": _matched([printed(vel.compute_retention(d, length=ell), ORACLE_DD_ROUND["t7"])
                        for d in ORACLE_DD_TABLE7["distances"] for ell in ORACLE_DD_TABLE7["lengths"]],
                       flat(ORACLE_DD_PRINTED_T7)),
        "t8": _matched([printed(vel.compute_manning_velocity(t9["depth"], t9["slope"], n), ORACLE_DD_ROUND["t9"])
                        for n in t9["n"]] + [f"{vel.compute_travel_time(t9['path_m'], t9['depth'], t9['slope'], n):.2f}"
                                             for n in t9["n"]],
                       list(ORACLE_DD_PRINTED_T9["velocity"]) + [f"{t:.2f}" for t in ORACLE_DD_PRINTED_T9["travel"]]),
    }
    with mp.workdps(ORACLE_REFERENCE_DPS):
        ratio = lambda d, k: ref.expected_clipped(min(mp.mpf(1), k * mp.mpf(str(d)))) / ref.expected_clipped(mp.mpf(str(d)))
        got7 = [(round(float(ratio(d, mp.mpf("1.1"))), 4), round(float(ratio(d, mp.mpf("0.9"))), 4))
                for d, _, _ in ORACLE_DD_PRINTED_T8]
    out["t7"] = _matched(got7, [(u, w) for _, u, w in ORACLE_DD_PRINTED_T8])
    for v in out.values():
        v["met"] = v["matched"] == v["of"]
    return out


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
            "max_err": max(abs(r) for r in res), "slope_min": slope_min}


def _unread(name):
    """Whether a config constant is read anywhere in src/."""
    out = subprocess.run(["git", "grep", "-l", name, "--", "src"], capture_output=True, text=True,
                         cwd=config.get_project_root())
    return not out.stdout.strip()


def draws_by_svd():
    """Whether NumPy's legacy multivariate normal draws are the SVD factor's (s3.5)."""
    c = np.array([[1, 0.5, 0.2], [0.5, 1, 0.3], [0.2, 0.3, 1]])
    x = np.random.RandomState(42).multivariate_normal(np.zeros(3), c, 4)
    z = np.random.RandomState(42).standard_normal((4, 3))
    _, s, v = np.linalg.svd(c)
    return bool(np.abs(x - z @ (np.sqrt(s)[:, None] * v)).max() == 0)


def assess(m, hydro_err, min_eig):
    """Each claim as a dict with its figures and ``met``."""
    ell = float(inspect.signature(m["velocity"].compute_retention).parameters["length"].default)
    quotes = [round(math.exp(-d / ell), 2) for d, _ in ORACLE_DD_PRINTED_S334]
    t10 = [round(math.exp(-ORACLE_DD_TABLE10["distance"] / x), 2) for x in ORACLE_DD_TABLE10["lengths"]]
    deg_err = 1 / math.cos(math.radians(ORACLE_DD_LATITUDE)) - 1
    n_mem, mem = ORACLE_DD_CLAIM_MEMORY
    poly = poly_fit()
    unread = [k for k in UNREAD if _unread(k)]
    hhi = float(m["risk"].calculate_hhi(np.ones(ORACLE_DD_PORTFOLIO_N)))
    return {
        **tables(m),
        "ell": {"code": ell, "doc": ORACLE_DD_DOC_ATTENUATION_M, "met": ell == ORACLE_DD_DOC_ATTENUATION_M},
        "quotes": {"values": quotes, "met": quotes == [q for _, q in ORACLE_DD_PRINTED_S334]
                   and t10 == list(ORACLE_DD_PRINTED_T10)},
        "deg": {"error": deg_err, "met": round(deg_err, 2) == ORACLE_DD_CLAIM_DEG_ERR},
        "unread": {"unread": unread, "met": unread == list(UNREAD)},
        "once": {"err": hydro_err, "met": hydro_err <= 1e-4},
        "svd": {"met": draws_by_svd()},
        "psd": {"min_eig": min_eig, "met": min_eig > 0},
        "memory": {"bytes": n_mem ** 2 * 8, "met": n_mem ** 2 * 8 == mem},
        "hhi": {"value": hhi, "met": abs(hhi - 1 / ORACLE_DD_PORTFOLIO_N) < 1e-15},
        "poly": {**{k: float(v) for k, v in poly.items()},
                 "met": all(abs(float(poly[k]) - v) <= 0.5e-6 for k, v in POLY_STATED.items())
                 and poly["slope_min"] > 0},
    }
