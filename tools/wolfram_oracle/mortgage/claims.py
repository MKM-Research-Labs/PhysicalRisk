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

"""MP-001's document, tested as stated (``mortgage_pricer_v1.3.pdf``).

* Eqs. 19, 22, 24 -- the fair value is the PV of expected cashflows, whose recovery
  is already net of the loss; measured against the pathwise value, which Wolfram
  computes independently. v0.1 found v1.1 deducting the loss a second time.
* Eqs. 18-19 -- the loss is taken on the balance owed when the month of default
  began, so the recovery is min(B_{i-1}, R) and never exceeds the property.
* s6, Table 7 -- the spread and value by flood category, at the document's baseline.
* s6.1 -- a 100 bp rise in the rate raises the payment by 8-12% on a 25-year term.
* s3.2.4 -- missing income prices at the top of the spread schedule.
* s7.2.2 -- total undiscounted expected loss is at most the loan.
* s5.3 / s7.2.1 -- at the contractual rate the contractual payments are worth par;
  Wolfram proves the identity symbolically.
"""

import mpmath as mp

from config.models import (
    ORACLE_MP_BASELINE,
    ORACLE_MP_CLAIM_RATE_GRID,
    ORACLE_MP_CLAIM_RATE_STEP,
    ORACLE_MP_CLAIM_TABLE7,
    ORACLE_MP_CLAIM_ZERO_INCOME_NODE,
    ORACLE_MP_REL_TOL,
)


def _payment(rate, years, p=1):
    r, n = mp.mpf(rate) / 12, years * 12
    return p * r / (1 - (1 + r) ** -n)


def assess(rows, pricer, wl=None):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    worst = max(rows, key=lambda r: r["correction"])
    path_err = max(r["fv_rel_err"] for r in rows)
    lp = pricer.LoanPricer()
    table7 = []
    for cat, spread_pct, value in ORACLE_MP_CLAIM_TABLE7:
        got = lp.price_loan(**ORACLE_MP_BASELINE, flood_risk_category=cat)
        table7.append((cat, spread_pct, value, 100 * got["credit_spread"], got["mortgage_value"],
                       got["pv_losses"]))
    steps = [float(_payment(r + 0.01, 25) / _payment(r, 25) - 1) for r in ORACLE_MP_CLAIM_RATE_GRID]
    lo, hi = ORACLE_MP_CLAIM_RATE_STEP
    base = ORACLE_MP_BASELINE
    zero = lp.price_loan(**{**base, "gross_annual_income": 0.0})["credit_spread"]
    top = ORACLE_MP_CLAIM_ZERO_INCOME_NODE * (1 + (base["current_term"] - base["original_maturity"] / 2) / 100)
    par = None if wl is None else wl.get("claim/par") == "1"
    return [
        {"claim": "Eqs. 19, 22, 24 fair value", "worst": path_err, "correction": worst["correction"],
         "at": worst["id"], "v11": float(worst["v11_fv"]), "fv": float(worst["fv_ref"]),
         "loan": worst["loan_amount"], "share": sum(r["correction"] > 0 for r in rows) / len(rows),
         "met": path_err <= ORACLE_MP_REL_TOL},
        {"claim": "Eqs. 18-19 recovery", "worst": max(r["excess_recovery"] for r in rows),
         "met": max(r["excess_recovery"] for r in rows) == 0},
        {"claim": "s6 Table 7", "rows": table7, "lgd_free": all(t[5] == 0 for t in table7),
         "met": all(round(t[3], 2) == t[1] and abs(t[4] - t[2]) <= 0.5 for t in table7)},
        {"claim": "s6.1 payment", "low": min(steps), "high": max(steps),
         "met": all(lo <= s <= hi for s in steps)},
        {"claim": "s3.2.4 missing income", "got": zero, "stated": top, "met": abs(zero - top) < 1e-12},
        {"claim": "s7.2.2 loss bound", "worst": max(r["el_over_par"] for r in rows),
         "met": max(r["el_over_par"] for r in rows) <= 1},
        {"claim": "s5.3 / s7.2.1 par", "identity": par, "met": par is not False},
    ]


def wl_claim_items():
    return [("claim/par", "If[FullSimplify[Sum[p r/(1 - (1 + r)^-n) (1 + r)^-i, {i, 1, n}] == p, "
                          "r > 0 && n > 0 && Element[n, Integers]], 1, 0]")]
