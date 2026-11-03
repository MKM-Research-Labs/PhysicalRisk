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
"""FPO-001's document, tested as stated.

Its printed coefficients and envelope against the code and the storm catalogue; its
probability table against the code; its statements about the surface -- the step at
severe, the floor, monotone in the level -- against the code; and its held-out
accuracy table against the GBM classifiers, recomputed with the document's model.
"""

import math

import numpy as np

from config.models import (
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_ENVELOPE,
    ORACLE_FPO_DOC_FLOOR,
    ORACLE_FPO_DOC_HOURS,
    ORACLE_FPO_DOC_TERMS,
    ORACLE_FPO_ENVELOPE_TOL,
    ORACLE_FPO_EARLY_RISE,
    ORACLE_FPO_FINE_LEVELS,
    ORACLE_FPO_LATE_HOUR,
    ORACLE_FPO_PRINTED_FIT,
    ORACLE_FPO_PRINTED_GRID,
    ORACLE_FPO_PRINTED_HELD,
    ORACLE_FPO_PRINTED_STATES,
    ORACLE_FPO_PRINTED_T0,
    ORACLE_FPO_T_HOURS,
    ORACLE_FPO_T_LEVELS,
    ORACLE_FPO_T_SEVERE,
)
from tools.wolfram_oracle.floodpoly import gbm


def predict(h, t):
    """The document's surface below severe over arrays of (h, t), in double precision."""
    c = [float(x) for x in ORACLE_FPO_DOC_COEFFS]
    hh = np.log([float(r) for r, _ in ORACLE_FPO_DOC_ENVELOPE])
    tt = np.log((np.array([float(x) for _, x in ORACLE_FPO_DOC_ENVELOPE]) + 1) / ORACLE_FPO_DOC_HOURS)
    h = np.maximum(h, np.log(float(ORACLE_FPO_DOC_FLOOR)))
    t = np.maximum(t, np.interp(h, hh, tt, left=-np.inf))
    z = sum(ci * h ** i * t ** j for (i, j), ci in zip(ORACLE_FPO_DOC_TERMS, c))
    return np.where(h >= 0, 1.0, 1 / (1 + np.exp(-np.clip(z, -30, 30))))


def _grid(poly):
    s, got, held = ORACLE_FPO_T_SEVERE, [], set()
    for lv in ORACLE_FPO_T_LEVELS:
        got.append([round(poly.p_flood_poly(lv * s, hr, s), 3) for hr in ORACLE_FPO_T_HOURS])
        held |= {(lv, hr) for hr in ORACLE_FPO_T_HOURS
                 if lv < 1 and math.log((hr + 1) / ORACLE_FPO_DOC_HOURS) < poly.envelope_t(math.log(lv))}
    matched = sum(abs(a - b) < 5e-4 for ra, rb in zip(got, ORACLE_FPO_PRINTED_GRID) for a, b in zip(ra, rb))
    return {"matched": int(matched), "of": len(ORACLE_FPO_T_LEVELS) * len(ORACLE_FPO_T_HOURS),
            "held": held == set(ORACLE_FPO_PRINTED_HELD), "n_held": len(held)}


def _surface(poly):
    """The code over every hour: the step at severe, the floor, and the smallest rise in P
    between neighbouring levels."""
    s, n = ORACLE_FPO_T_SEVERE, ORACLE_FPO_FINE_LEVELS
    floor = float(ORACLE_FPO_DOC_FLOOR)
    drop, at_floor, step, by_hour = 0.0, 0.0, True, []
    for hr in range(ORACLE_FPO_DOC_HOURS):
        ps = [poly.p_flood_poly(s * k / n, hr, s) for k in range(1, n + 1)]
        by_hour.append(ps)
        drop = max(drop, max(a - b for a, b in zip(ps, ps[1:])))
        at_floor = max(at_floor, poly.p_flood_poly(s * floor, hr, s))
        step &= all(poly.p_flood_poly(s * r, hr, s) == 1.0 for r in (1.0, 1.05, 1.5))
        step &= poly.p_flood_poly(s * 0.1, hr, s) == poly.p_flood_poly(s * floor, hr, s)
    rises = [max(b - a for a, b in zip(col, col[1:])) for col in zip(*by_hour)]       # level by level, hour to hour
    late = max(max(b - a for a, b in zip(col[ORACLE_FPO_LATE_HOUR:], col[ORACLE_FPO_LATE_HOUR + 1:]))
               for col in zip(*by_hour))
    return {"drop": drop, "at_floor": at_floor, "step": step, "late_rise": late, "early_rise": max(rises)}


def _envelope(top):
    """Each printed knot's hour, recomputed from the catalogue."""
    got = [gbm.first_reached(top, float(r)) for r, _ in ORACLE_FPO_DOC_ENVELOPE[1:]]
    worst = max(abs(g - float(h)) if g is not None else math.inf for g, (_, h) in zip(got, ORACLE_FPO_DOC_ENVELOPE[1:]))
    first = round(float(top[0]), 3)
    return {"worst": worst, "first": first,
            "met": worst <= ORACLE_FPO_ENVELOPE_TOL and first == float(ORACLE_FPO_DOC_ENVELOPE[0][0])}


def _fit(held):
    """The held-out table as printed (MAE and bias to 4 dp, the share to the percent)."""
    def same(r, p):
        return (abs(r[0] - p[0]) < 5e-5 and abs(r[1] - p[1]) < 5e-5 and abs(100 * r[2] - p[2]) < 0.5
                and abs(r[3] - p[3]) < 5e-5)
    matched = sum(same(r, p) for r, p in zip(held["rows"], ORACLE_FPO_PRINTED_FIT))
    states = (held["fit_states"], held["test_states"])
    return {"matched": int(matched), "of": len(ORACLE_FPO_PRINTED_FIT), "states": states,
            "met": matched == len(held["rows"]) == len(ORACLE_FPO_PRINTED_FIT) and states == ORACLE_FPO_PRINTED_STATES}


def assess(poly, top, held, scenario_text):
    """Each claim as a dict with its figures and ``met``."""
    coeffs = [f"{c:.6f}" for c in poly.flood_poly_coeffs] == [f"{float(c):.6f}" for c in ORACLE_FPO_DOC_COEFFS]
    knots = [tuple(k) for k in poly.flood_poly_envelope] == [(float(r), float(h)) for r, h in ORACLE_FPO_DOC_ENVELOPE]
    t0 = math.log(1 / ORACLE_FPO_DOC_HOURS)
    surface = _surface(poly)
    latch = "severe_breached = True" in scenario_text and "if severe_breached:" in scenario_text
    return {
        "coeffs": {"met": coeffs and list(poly.flood_poly_terms) == list(ORACLE_FPO_DOC_TERMS)},
        "envelope": {**_envelope(top), "config": knots},
        "grid": {**(g := _grid(poly)), "met": g["matched"] == g["of"] and g["held"]},
        "step": {"met": surface["step"]},
        "floor": {"value": surface["at_floor"], "met": surface["at_floor"] < 0.01},
        "monotone": {"drop": surface["drop"], "met": surface["drop"] <= 0.0},
        "in_time": {"late": surface["late_rise"], "early": surface["early_rise"],
                    "met": surface["late_rise"] <= 0.0 and surface["early_rise"] <= ORACLE_FPO_EARLY_RISE},
        "t0": {"value": t0, "met": round(t0, 2) == ORACLE_FPO_PRINTED_T0},
        "fit": _fit(held),
        "latch": {"met": latch},
    }
