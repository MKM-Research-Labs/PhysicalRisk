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

"""EF-001's document, tested as stated (``event_frequency_plan.pdf`` v2.3).

* s5.9 -- E[(1-p)^N] = exp(-lambda p) for N ~ Poisson(lambda): the closed form
  is the simulation's exact expectation, and the aggregate view lambda p is never
  below it. Wolfram checks the identity symbolically.
* s5.9 -- the gate statistic is a true z-score, so mean |z| = sqrt(2/pi) = 0.798.
* s7.2 -- the sampling error at 1e3..1e6 simulated years scales as 1/sqrt(n).
* annualise.py / gev.py -- the multi-year term structure compounds the annual
  *probability* as if it were a rate; measured against the exact tenor probability.
* annualise.py -- 1 - exp(-x) against -expm1(-x) for small lambda p.
* families -- the Negative Binomial search reaches the likelihood maximum.
"""

import mpmath as mp

from config.models import (
    ORACLE_EF_CLAIM_MEAN_ABS_Z,
    ORACLE_EF_CLAIM_SAMPLING,
    ORACLE_EF_LL_TOL,
    ORACLE_EF_OPERATING_MIN_X,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import wl_number


def assess(rows, wl=None):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    annual = [r for r in rows if r["group"] == "annual"]
    small = max((r["rel_err"] for r in annual if r["lam"] * r["p"] < ORACLE_EF_OPERATING_MIN_X), default=0.0)
    agg = all(float(r["lam"] * r["p"]) >= float(mp.mpf(r["ref"])) for r in annual)
    mean_abs_z = float(mp.sqrt(2 / mp.pi) if wl is None else wl_number(wl["claim/mean_abs_z"]))
    first_n, first_e = ORACLE_EF_CLAIM_SAMPLING[0]
    scaled = [(n, e, first_e * (first_n / n) ** 0.5) for n, e in ORACLE_EF_CLAIM_SAMPLING]
    sampling_ok = all(abs(s / e - 1) <= 0.05 for _, e, s in scaled)
    gaps = [r["convention_gap"] for r in rows if r["group"] == "term"]
    nb_gap = max(r.get("ll_gap", 0.0) for r in rows)
    eq4 = None if wl is None else wl.get("claim/eq4") == "1"
    return [
        {"claim": "s5.9 closed form", "identity": eq4, "aggregate_ge_occurrence": agg,
         "met": agg and (eq4 is not False)},
        {"claim": "s5.9 mean |z|", "exact": mean_abs_z, "stated": ORACLE_EF_CLAIM_MEAN_ABS_Z,
         "met": round(mean_abs_z, 3) == ORACLE_EF_CLAIM_MEAN_ABS_Z},
        {"claim": "s7.2 sampling error", "scaled": scaled,
         "implied_p": 1 / (1 + first_n * first_e ** 2), "met": sampling_ok},
        {"claim": "term structure convention", "low": max(gaps), "high": min(gaps), "met": None},
        {"claim": "annualisation precision", "worst": small, "below": ORACLE_EF_OPERATING_MIN_X,
         "met": None},
        {"claim": "NegBin maximum", "worst": nb_gap, "limit": ORACLE_EF_LL_TOL,
         "met": nb_gap <= ORACLE_EF_LL_TOL},
    ]


def wl_claim_items():
    d = ORACLE_WOLFRAM_DIGITS
    return [
        ("claim/eq4", "If[Simplify[Expectation[(1 - p)^n, n \\[Distributed] PoissonDistribution[l]] "
                      "== Exp[-l p], l > 0 && 0 <= p <= 1], 1, 0]"),
        ("claim/mean_abs_z", f"N[Expectation[Abs[z], z \\[Distributed] NormalDistribution[0, 1]], {d}]"),
    ]


def operating(rows):
    """Annualisation rows inside the operating range (lambda p at least the floor)."""
    return [r for r in rows if r["group"] != "annual" or r["lam"] * r["p"] >= ORACLE_EF_OPERATING_MIN_X]

