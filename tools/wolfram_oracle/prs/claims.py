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

"""The model document's own claims about PR-001, tested as stated.

Three statements in ``prs_pricing.pdf`` are numerical and can be checked against
the exact spreads the benchmark computes:

* s8.3 — quarterly discretisation against continuous time: "accurate" for low
  annual rates, "up to 2-3 bp" when the rate exceeds 0.20;
* s8.4 — flat against term-structure discounting: "< 1 bp" on a 5-year PRS;
* s3.3 — the basis compares the gauge's spread with the property's. The code
  (``src/port/.../pricing/_basis.py``) takes the gauge leg as p x 10^4 while the
  property leg is Eq. 7, so the two legs differ at the same probability.

Every figure comes from the 50-digit reference rows, at R = 0, which is what the
book trades (s3.2).
"""

import mpmath as mp

from config.models import (
    ORACLE_PRS_BPS,
    ORACLE_PRS_CLAIM_CURVE_BP,
    ORACLE_PRS_CLAIM_CURVE_TENOR,
    ORACLE_PRS_CLAIM_DISC_BP,
    ORACLE_PRS_CLAIM_DISC_SPLIT,
    ORACLE_PRS_CLAIM_MAX_P,
    ORACLE_PRS_TABLE_TENOR,
)


def _row(rows, curve, tenor, p):
    return next(r for r in rows if r["curve"] == curve and r["T"] == tenor
                and r["R"] == 0.0 and r["p"] == p)


def by_probability(rows):
    """The worked table: for each p, at the table tenor and R = 0."""
    out = []
    for p in sorted({r["p"] for r in rows if r["p"] <= ORACLE_PRS_CLAIM_MAX_P}):
        flat = _row(rows, "flat", ORACLE_PRS_TABLE_TENOR, p)
        book = _row(rows, "book", ORACLE_PRS_TABLE_TENOR, p)
        disc, cont = mp.mpf(flat["ref"]), mp.mpf(flat["continuous"])
        out.append({
            "p": p, "quarterly": float(disc), "continuous": float(cont),
            "disc_minus_cont_bp": float(disc - cont),
            "disc_rel": float(disc / cont - 1),
            "book": float(mp.mpf(book["ref"])),
            "flat_minus_book_bp": float(disc - mp.mpf(book["ref"])),
            "gauge_leg": p * ORACLE_PRS_BPS,
            "basis_artefact_bp": float(p * ORACLE_PRS_BPS - mp.mpf(book["ref"])),
        })
    return out


def _first_over(table, key, limit):
    over = [t["p"] for t in table if abs(t[key]) > limit]
    return min(over) if over else None


def assess(rows):
    """Each claim as (claim, result, met, worst) — met is None for a finding."""
    in_range = [r for r in rows if r["p"] <= ORACLE_PRS_CLAIM_MAX_P]
    low = max(abs(r["disc_minus_cont_bp"]) for r in in_range
              if r["p"] <= ORACLE_PRS_CLAIM_DISC_SPLIT)
    high = max(abs(r["disc_minus_cont_bp"]) for r in in_range
               if r["p"] > ORACLE_PRS_CLAIM_DISC_SPLIT)
    curve_rows = [(r["p"], mp.mpf(r["ref"]) - mp.mpf(_row(rows, "book", r["T"], r["p"])["ref"]))
                  for r in in_range if r["curve"] == "flat" and r["R"] == 0.0
                  and r["T"] == ORACLE_PRS_CLAIM_CURVE_TENOR]
    curve_worst = max(abs(float(d)) for _, d in curve_rows)
    curve_over = min((p for p, d in curve_rows if abs(d) > ORACLE_PRS_CLAIM_CURVE_BP),
                     default=None)
    table = by_probability(rows)
    basis_over = _first_over(table, "basis_artefact_bp", ORACLE_PRS_CLAIM_CURVE_BP)
    return [
        {"claim": "s8.3 discretisation", "low": low, "high": high,
         "limit": ORACLE_PRS_CLAIM_DISC_BP,
         "met": max(low, high) <= ORACLE_PRS_CLAIM_DISC_BP},
        {"claim": "s8.4 flat curve", "worst": curve_worst, "first_over": curve_over,
         "limit": ORACLE_PRS_CLAIM_CURVE_BP, "met": curve_worst <= ORACLE_PRS_CLAIM_CURVE_BP},
        {"claim": "s3.3 basis legs", "first_over": basis_over,
         "worst": max(abs(t["basis_artefact_bp"]) for t in table), "met": None},
    ]
