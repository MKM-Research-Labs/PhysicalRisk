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

"""The PRS fair spread: PR-001's own code vs a 50-digit reference and Wolfram.

The reference implements the model document (``prs_pricing.pdf``, s3.1), not the
code: annual probability capped at 0.999 and converted by lambda = -ln(1 - p)
(Eq. 1); survival exp(-lambda t) and discount exp(-r(t) t) (Eqs. 2-3); quarterly
dates (s3.1.3); the risky annuity A = sum dt S(t_i) D(t_i) (Eq. 4); protection
P = sum (1-R) (S(t_{i-1}) - S(t_i)) D(t_i - dt/2), paid at the period midpoint
(Eq. 5); s = 10^4 P / A (Eq. 7), floored at the minimum spread (Eq. 8).

The rate r(t) is either flat or the book's yield curve, interpolated linearly
between whole-year points and held flat beyond them, as the code documents.

In continuous time, with a constant hazard rate, both legs integrate the same
S(t) D(t), so the fair spread is exactly (1 - R) lambda whatever the curve. That
closed form is the continuous benchmark the document's s8.3 is about.
"""

import mpmath as mp

from config.models import (
    MIN_PRS_SPREAD_BPS,
    ORACLE_PRS_BPS,
    ORACLE_PRS_FLAT_RATE,
    ORACLE_PRS_INTERP_MAX_T,
    ORACLE_PRS_INTERP_STEP,
    ORACLE_PRS_INTERP_TOL,
    ORACLE_PRS_PERIODS_PER_YEAR,
    ORACLE_PRS_PROB_CAP,
    ORACLE_PRS_PROBS,
    ORACLE_PRS_RECOVERIES,
    ORACLE_PRS_TABLE_TENOR,
    ORACLE_PRS_TENORS,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from config.port import DEFAULT_YIELD_CURVE
from tools.wolfram_oracle._wl import rel_err, wl_exact, wl_number, wl_precise

# Curve name -> curve, as the model takes it (None means the flat rate).
CURVES = {"flat": None, "book": DEFAULT_YIELD_CURVE}


def curve_rate(curve, t):
    """r(t): flat, or linear between whole-year points and flat beyond them."""
    t = mp.mpf(t)
    if not curve:
        return mp.mpf(ORACLE_PRS_FLAT_RATE)
    knots = sorted((int(k), mp.mpf(v)) for k, v in curve.items())
    if t <= knots[0][0]:
        return knots[0][1]
    for (a, ra), (b, rb) in zip(knots, knots[1:]):
        if t <= b:
            return ra + (rb - ra) * (t - a) / (b - a)
    return knots[-1][1]


def hazard(p):
    """Eq. 1, after the s3.1.1 cap."""
    return -mp.log(1 - mp.mpf(min(p, ORACLE_PRS_PROB_CAP)))


def discrete_ref(p, tenor, recovery, curve):
    """Eqs. 1-7: the unfloored fair spread in bp."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        lam, dt = hazard(p), mp.mpf(1) / ORACLE_PRS_PERIODS_PER_YEAR
        times = [i * dt for i in range(ORACLE_PRS_PERIODS_PER_YEAR * tenor + 1)]
        annuity = mp.fsum(dt * mp.exp(-lam * t) * mp.exp(-curve_rate(curve, t) * t)
                          for t in times[1:])
        protection = mp.fsum(
            (1 - mp.mpf(recovery)) * (mp.exp(-lam * a) - mp.exp(-lam * b))
            * mp.exp(-curve_rate(curve, b - dt / 2) * (b - dt / 2))
            for a, b in zip(times, times[1:]))
        return ORACLE_PRS_BPS * protection / annuity


def continuous_ref(p, recovery):
    """The continuous-time spread in bp: exactly (1 - R) lambda."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return ORACLE_PRS_BPS * (1 - mp.mpf(recovery)) * hazard(p)


def run(pricing):
    """Every case of the grid: the model, the reference, and the continuous spread."""
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for name, curve in CURVES.items():
            for tenor in ORACLE_PRS_TENORS:
                for recovery in ORACLE_PRS_RECOVERIES:
                    for p in ORACLE_PRS_PROBS:
                        model = float(pricing.compute_prs_spread(
                            p, tenor, recovery, risk_free_rate=ORACLE_PRS_FLAT_RATE,
                            yield_curve=curve))
                        ref = discrete_ref(p, tenor, recovery, curve)
                        expected = max(ref, mp.mpf(MIN_PRS_SPREAD_BPS))  # Eq. 8
                        cont = continuous_ref(p, recovery)
                        rows.append({
                            "id": f"{name}/T={tenor}/R={recovery}/p={p}", "curve": name,
                            "T": tenor, "R": recovery, "p": p, "model": repr(model),
                            "ref": mp.nstr(ref, 30), "floored": bool(ref < MIN_PRS_SPREAD_BPS),
                            "rel_err": rel_err(model, expected),
                            "continuous": mp.nstr(cont, 30),
                            "disc_minus_cont_bp": float(ref - cont),
                        })
    return rows


def rules(pricing):
    """The rules around the formula, each as (rule, holds, detail)."""
    floor_rows = [p for p in ORACLE_PRS_PROBS
                  if discrete_ref(p, 1, 0.0, None) < MIN_PRS_SPREAD_BPS]
    grid = [i * ORACLE_PRS_INTERP_STEP
            for i in range(int(ORACLE_PRS_INTERP_MAX_T / ORACLE_PRS_INTERP_STEP) + 1)]
    interp = max(abs(mp.mpf(pricing.interpolate_yield_rate(DEFAULT_YIELD_CURVE, t))
                     - curve_rate(DEFAULT_YIELD_CURVE, t)) for t in grid)
    above_cap = (ORACLE_PRS_PROB_CAP + 1) / 2  # between the cap and certainty
    capped = pricing.compute_prs_spread(above_cap, ORACLE_PRS_TABLE_TENOR)
    return [
        ("A zero probability prices at zero (s5.3.1)",
         pricing.compute_prs_spread(0.0, ORACLE_PRS_TABLE_TENOR) == 0.0, "0 bp, no floor"),
        ("The floor binds below 2 bp (Eq. 8)",
         all(pricing.compute_prs_spread(p, 1) == MIN_PRS_SPREAD_BPS for p in floor_rows),
         "p = " + ", ".join(f"{p:g}" for p in floor_rows) + " priced at the floor"),
        ("Probabilities above 0.999 price as 0.999 (s3.1.1)",
         capped == pricing.compute_prs_spread(ORACLE_PRS_PROB_CAP, ORACLE_PRS_TABLE_TENOR),
         f"p = {above_cap} prices as p = {ORACLE_PRS_PROB_CAP}"),
        ("Yield curve: linear between years, flat beyond",
         interp <= ORACLE_PRS_INTERP_TOL, f"max difference {float(interp):.1e} over {len(grid)} times"),
    ]


def _wl_rate(curve):
    """r(t) as a Wolfram Function, piece for piece as ``curve_rate``."""
    if not curve:
        return f"Function[t, {wl_precise(ORACLE_PRS_FLAT_RATE)}]"
    knots = sorted((int(k), wl_precise(v)) for k, v in curve.items())
    pieces = [f"{{{knots[0][1]}, t <= {knots[0][0]}}}"]
    pieces += [f"{{{ra} + ({rb} - {ra}) (t - {a})/{b - a}, t <= {b}}}"
               for (a, ra), (b, rb) in zip(knots, knots[1:])]
    return f"Function[t, Piecewise[{{{', '.join(pieces)}}}, {knots[-1][1]}]]"


def wl_items(rows):
    """Eqs. 1-7 as exact Wolfram sums, at 60-digit input precision."""
    k, d = ORACLE_PRS_PERIODS_PER_YEAR, ORACLE_WOLFRAM_DIGITS
    items = []
    for r in rows:
        head = (f"Module[{{lam = -Log[1 - Min[{wl_precise(r['p'])}, {wl_exact(ORACLE_PRS_PROB_CAP)}]], "
                f"rr = {_wl_rate(CURVES[r['curve']])}, n = {k * r['T']}, "
                f"rec = {wl_precise(r['R'])}}}, ")
        prot = (f"(1 - rec) Sum[(Exp[-lam (i - 1)/{k}] - Exp[-lam i/{k}]) "
                f"Exp[-rr[(2 i - 1)/{2 * k}] (2 i - 1)/{2 * k}], {{i, 1, n}}]")
        ann = f"Sum[Exp[-lam i/{k}] Exp[-rr[i/{k}] i/{k}]/{k}, {{i, 1, n}}]"
        items.append((r["id"], f"{head}N[{ORACLE_PRS_BPS} {prot}/{ann}, {d}]]"))
    return items


def add_wolfram(rows, wl):
    """Annotate each row with Wolfram's spread and both comparisons."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            w = wl_number(wl[r["id"]])
            r["wolfram"] = mp.nstr(w, 30)
            r["wolfram_vs_ref"] = rel_err(w, r["ref"])
            expected = max(w, mp.mpf(MIN_PRS_SPREAD_BPS))
            r["model_vs_wolfram"] = rel_err(r["model"], expected)
    return rows
