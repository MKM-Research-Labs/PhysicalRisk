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

Its printed tables against the code; its statements about the surface against the
code; its accuracy claims against the GBM classifiers on real storm states; and what
production does with the model that the document does not say.
"""

import numpy as np
from scipy.optimize import least_squares

from config.models import (
    ORACLE_FPO_CLAIM_DELTA,
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_HOURS,
    ORACLE_FPO_DOC_TERMS,
    ORACLE_FPO_PRINTED_AT_SEVERE,
    ORACLE_FPO_PRINTED_CUBIC_R2,
    ORACLE_FPO_PRINTED_FIT,
    ORACLE_FPO_PRINTED_T0,
    ORACLE_FPO_PRINTED_T1,
    ORACLE_FPO_PRINTED_T2,
    ORACLE_FPO_T1_HOURS,
    ORACLE_FPO_T1_LEVELS,
    ORACLE_FPO_T1_SEVERE,
)

CUBIC = ((1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (3, 0), (0, 3), (2, 1), (1, 2), (0, 0))


def predict(h, t, terms=ORACLE_FPO_DOC_TERMS, coeffs=ORACLE_FPO_DOC_COEFFS):
    """The document's surface over arrays of (h, t), in double precision."""
    z = sum(float(c) * h ** i * t ** j for (i, j), c in zip(terms, coeffs))
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def fit_cubic(h, t, g):
    """The least-squares cubic kernel through the same states (s9.1's alternative)."""
    F = np.column_stack([h ** i * t ** j for i, j in CUBIC])
    b = least_squares(lambda c: 1 / (1 + np.exp(-np.clip(F @ c, -30, 30))) - g, np.zeros(len(CUBIC))).x
    return lambda hh, tt: predict(hh, tt, CUBIC, b)


def _tables(poly, classifier):
    s = ORACLE_FPO_T1_SEVERE
    got1 = [[round(poly.p_flood_poly(w, hr, s), 2) for hr in ORACLE_FPO_T1_HOURS] for w in ORACLE_FPO_T1_LEVELS]
    t1 = sum(abs(a - b) < 0.005 for ra, rb in zip(got1, ORACLE_FPO_PRINTED_T1) for a, b in zip(ra, rb))
    t2_poly = [round(poly.p_flood_poly(w, hr, s), 2) for w, hr, _, _ in ORACLE_FPO_PRINTED_T2]
    X = np.array([[np.log(w / s), np.log((hr + 1) / ORACLE_FPO_DOC_HOURS), 0, 0] for w, hr, _, _ in ORACLE_FPO_PRINTED_T2])
    t2_gbm = [round(float(v), 2) for v in classifier.predict_proba(X)[:, 1]]
    return {"t1": {"matched": int(t1), "of": 54, "at_severe": got1[ORACLE_FPO_T1_LEVELS.index(s)],
                   "met": t1 == 54},
            "t2": {"poly": t2_poly, "gbm": t2_gbm,
                   "matched": sum(abs(a - r[3]) < 0.005 for a, r in zip(t2_poly, ORACLE_FPO_PRINTED_T2)),
                   "gbm_matched": sum(abs(a - r[2]) < 0.005 for a, r in zip(t2_gbm, ORACLE_FPO_PRINTED_T2)),
                   "met": False}}


def assess(poly, classifier, gauges, fit):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    out = _tables(poly, classifier)
    out["t2"]["met"] = out["t2"]["matched"] == len(ORACLE_FPO_PRINTED_T2) == out["t2"]["gbm_matched"]
    t0 = float(np.log(1 / ORACLE_FPO_DOC_HOURS))
    near_p95 = max(g["near"]["p95"] for g in gauges)
    out.update({
        "t0": {"value": t0, "met": round(t0, 1) == ORACLE_FPO_PRINTED_T0},
        "at_severe": {"code": (out["t1"]["at_severe"][0], out["t1"]["at_severe"][-1]),
                      "met": tuple(out["t1"]["at_severe"][i] for i in (0, -1)) == ORACLE_FPO_PRINTED_AT_SEVERE},
        "delta": {"near_p95": near_p95, "share": max(g["near"]["over05"] for g in gauges),
                  "met": near_p95 < ORACLE_FPO_CLAIM_DELTA},
        "fit": {**fit, "met": all(abs(fit[k] - v) < 0.0005 for k, v in ORACLE_FPO_PRINTED_FIT.items())},
        "cubic": {"r2": fit.get("cubic_r2"), "met": fit.get("cubic_r2") is not None
                  and abs(fit["cubic_r2"] - ORACLE_FPO_PRINTED_CUBIC_R2) < 0.005},
        "conservative": {"bias": [g["near"]["bias"] for g in gauges],
                         "met": all(g["near"]["bias"] >= 0 for g in gauges)},
        "latch": {"met": None},
        "simple": {"met": None},
    })
    return out
