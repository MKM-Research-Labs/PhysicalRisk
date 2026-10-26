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

"""DE-001's model document and code, tested as stated.

* s6 item 5 -- the 1 bp forward difference is within 0.01 bp of the gradient;
* s6 item 1 -- FS01 "scales approximately linearly with hazard rate" (50-500 bp);
* s6 item 2 -- a 5Y trade has "approximately 4.5x" the FS01 of a 1Y;
* s6 item 3 -- a 100 bp parallel yield shift changes FS01 by "approximately 3-5%";
* s7.2 -- the hand-calculated annuity, 3Y at 200 bp and 4% flat, "~2.738";
* s8 item 1 -- FS01 x dh against full revaluation for a 50 bp move;
* the 2 bp spread floor, under which the forward difference sees no move;
* s3.5 -- basis delta "~ gauge delta": the code ignores the basis it is given.

FS01 is the document's forward difference, from the 50-digit reference, on the
flat curve and at R = 0 unless stated.
"""

import mpmath as mp

from config.models import (
    ORACLE_DE_CLAIM_FD_BP,
    ORACLE_DE_CLAIM_HAND,
    ORACLE_DE_CLAIM_HAND_DP,
    ORACLE_DE_CLAIM_LINEAR,
    ORACLE_DE_CLAIM_LINEAR_TOL,
    ORACLE_DE_CLAIM_MOVE,
    ORACLE_DE_CLAIM_TENOR,
    ORACLE_DE_CLAIM_YIELD_RANGE,
    ORACLE_DE_CLAIM_YIELD_SHIFT,
    ORACLE_DE_FLAT_RATE,
    ORACLE_DE_RATES,
    ORACLE_DE_TABLE_TENOR,
    ORACLE_DE_TENORS,
    ORACLE_PRS_BPS,
    ORACLE_WOLFRAM_DIGITS,
)
from config.port import BUMP_1BP
from tools.wolfram_oracle._wl import wl_precise
from tools.wolfram_oracle.delta.sensitivity import fs01, legs, wl_spread


def _row(rows, h, tenor, curve="flat"):
    return next(r for r in rows if r["curve"] == curve and r["T"] == tenor and r["h"] == h)


def assess(rows):
    """Each claim as a dict with its figures and ``met`` (None for a finding)."""
    lo_h, hi_h = ORACLE_DE_CLAIM_LINEAR
    linear = float(fs01(hi_h, ORACLE_DE_TABLE_TENOR, None) / fs01(lo_h, ORACLE_DE_TABLE_TENOR, None))
    short, long_, ratio, tol = ORACLE_DE_CLAIM_TENOR
    tenor = float(fs01(0.02, long_, None) / fs01(0.02, short, None))
    shifts = [float(fs01(h, t, None, shift=ORACLE_DE_CLAIM_YIELD_SHIFT) / fs01(h, t, None) - 1)
              for h in ORACLE_DE_RATES for t in ORACLE_DE_TENORS
              if t <= ORACLE_DE_TABLE_TENOR and not _row(rows, h, t)["floored"]]
    h, t, r, stated = ORACLE_DE_CLAIM_HAND
    hand = float(legs(h, t, None, shift=r - ORACLE_DE_FLAT_RATE)[1])
    full = legs(0.02 + ORACLE_DE_CLAIM_MOVE, ORACLE_DE_TABLE_TENOR, None)[0] - legs(0.02, ORACLE_DE_TABLE_TENOR, None)[0]
    lin = mp.mpf(_row(rows, 0.02, ORACLE_DE_TABLE_TENOR)["gradient_bp"]) * ORACLE_DE_CLAIM_MOVE / BUMP_1BP
    lowest = _row(rows, min(ORACLE_DE_RATES), ORACLE_DE_TABLE_TENOR)
    fd = max(abs(r["fd_minus_gradient_bp"]) for r in rows)
    lo_y, hi_y = ORACLE_DE_CLAIM_YIELD_RANGE
    return [
        {"claim": "s6.5 bump error", "worst": fd, "limit": ORACLE_DE_CLAIM_FD_BP,
         "met": fd <= ORACLE_DE_CLAIM_FD_BP},
        {"claim": "s6.1 linear in h", "ratio": linear, "met": abs(linear / 10 - 1) <= ORACLE_DE_CLAIM_LINEAR_TOL},
        {"claim": "s6.2 tenor ratio", "ratio": tenor, "stated": ratio, "met": abs(tenor - ratio) <= tol},
        {"claim": "s6.3 yield shift", "low": min(abs(s) for s in shifts), "high": max(abs(s) for s in shifts),
         "sign": "falls" if max(shifts) < 0 else "moves",
         "met": all(lo_y <= abs(s) <= hi_y for s in shifts)},
        {"claim": "s7.2 hand calculation", "exact": hand, "stated": stated,
         "met": round(hand, ORACLE_DE_CLAIM_HAND_DP) == stated},
        {"claim": "s8.1 convexity", "rel": float(full / lin - 1), "met": None},
        {"claim": "floor", "h": min(ORACLE_DE_RATES), "model": lowest["delta_spread_bps_model"],
         "gradient": float(mp.mpf(lowest["gradient_bp"])), "met": None},
        {"claim": "s3.5 basis delta", "identical": all(r["basis_equals_gauge"] for r in rows), "met": None},
    ]


def by_rate(rows):
    """The FS01 table: for each h, the engine's FS01 at every tenor, flat curve."""
    return [[h] + [float(_row(rows, h, t)["dv01_gbp_model"]) for t in ORACLE_DE_TENORS]
            for h in ORACLE_DE_RATES]


def wl_claim_items():
    """The hand-calculated annuity, and FS01 before and after the yield shift."""
    d = ORACLE_WOLFRAM_DIGITS
    h, t, r, _ = ORACLE_DE_CLAIM_HAND
    _, an = wl_spread(None, t, shift=r - ORACLE_DE_FLAT_RATE)
    items = [("claim/hand_annuity", f"N[{an}[{wl_precise(h)}], {d}]")]
    for label, shift in (("base", 0), ("shifted", ORACLE_DE_CLAIM_YIELD_SHIFT)):
        sp, an = wl_spread(None, ORACLE_DE_TABLE_TENOR, shift=shift)
        x, up = wl_precise(0.02), wl_precise(0.02 + BUMP_1BP)  # the bumped double, as engine
        items.append((f"claim/fs01_{label}",
                      f"N[({sp}[{up}] - {sp}[{x}])/{ORACLE_PRS_BPS} {an}[{x}], {d}]"))
    return items
