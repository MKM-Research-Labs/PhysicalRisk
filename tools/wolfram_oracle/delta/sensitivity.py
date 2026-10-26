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

"""The delta engine's outputs: DE-001's own code vs a 50-digit reference and Wolfram.

The reference implements the model document (``delta_engine.pdf`` v1.0, s3) and,
for the spread it differences, PR-001's document (Eqs. 1-8):

* the risky annuity A(h, T) = sum dt S(t_i) D(t_i), quarterly, lambda = -ln(1 - h);
* FS01 = [s(h + 1 bp) - s(h)] / 10^4 x A(h, T) x N, s floored at 2 bp (s3.4);
* MTM = (s - s0) / 10^4 x A x N for a protection buyer (s3.3).

It also gives the exact gradient ds/dh, which the document says the 1 bp forward
difference approximates. The engine rounds what it returns, so those outputs are
judged to half a unit in their last place; the annuity is also checked unrounded.
"""

import mpmath as mp

from config.models import (
    MIN_PRS_SPREAD_BPS,
    ORACLE_DE_FLAT_RATE,
    ORACLE_DE_GRADIENT_STEP,
    ORACLE_DE_NOTIONAL,
    ORACLE_DE_RATES,
    ORACLE_DE_TENORS,
    ORACLE_DE_TRADE_SPREAD_BPS,
    ORACLE_PRS_BPS,
    ORACLE_PRS_PERIODS_PER_YEAR,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from config.port import BUMP_1BP, DEFAULT_YIELD_CURVE
from tools.wolfram_oracle._wl import rel_err, wl_number, wl_precise

CURVES = {"flat": None, "book": DEFAULT_YIELD_CURVE}


def rate(curve, t, shift=0):
    """r(t): flat, or linear between whole-year points and flat beyond; plus a shift."""
    t, shift = mp.mpf(t), mp.mpf(shift)
    if not curve:
        return mp.mpf(ORACLE_DE_FLAT_RATE) + shift
    knots = sorted((int(k), mp.mpf(v)) for k, v in curve.items())
    if t <= knots[0][0]:
        return knots[0][1] + shift
    for (a, ra), (b, rb) in zip(knots, knots[1:]):
        if t <= b:
            return ra + (rb - ra) * (t - a) / (b - a) + shift
    return knots[-1][1] + shift


def legs(h, tenor, curve, recovery=0, shift=0):
    """(unfloored spread in bp, risky annuity) at annual hazard rate h."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        lam, dt = -mp.log(1 - mp.mpf(h)), mp.mpf(1) / ORACLE_PRS_PERIODS_PER_YEAR
        ts = [i * dt for i in range(ORACLE_PRS_PERIODS_PER_YEAR * tenor + 1)]
        ann = mp.fsum(dt * mp.exp(-lam * t) * mp.exp(-rate(curve, t, shift) * t) for t in ts[1:])
        prot = mp.fsum((1 - mp.mpf(recovery)) * (mp.exp(-lam * a) - mp.exp(-lam * b))
                       * mp.exp(-rate(curve, b - dt / 2, shift) * (b - dt / 2))
                       for a, b in zip(ts, ts[1:]))
        return ORACLE_PRS_BPS * prot / ann, ann


def floored(s):
    return max(s, mp.mpf(MIN_PRS_SPREAD_BPS))


def gradient(h, tenor, curve, shift=0):
    """The exact ds/dh, unfloored, in bp per unit of h."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return mp.diff(lambda x: legs(x, tenor, curve, shift=shift)[0], mp.mpf(h),
                       h=mp.mpf(ORACLE_DE_GRADIENT_STEP))


def fs01(h, tenor, curve, shift=0, notional=ORACLE_DE_NOTIONAL, analytic=False):
    """FS01 in GBP: the document's forward difference, or the analytic gradient."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        s, ann = legs(h, tenor, curve, shift=shift)
        if analytic:
            ds = gradient(h, tenor, curve, shift) * mp.mpf(BUMP_1BP)
        else:
            ds = floored(legs(h + BUMP_1BP, tenor, curve, shift=shift)[0]) - floored(s)
        return ds / ORACLE_PRS_BPS * ann * notional


def run(pricer):
    """Every case: the engine's annuity, delta, basis delta and MTM against the reference."""
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for name, curve in CURVES.items():
            for tenor in ORACLE_DE_TENORS:
                for h in ORACLE_DE_RATES:
                    s, ann = legs(h, tenor, curve)
                    s_up = legs(h + BUMP_1BP, tenor, curve)[0]
                    grad = gradient(h, tenor, curve) * mp.mpf(BUMP_1BP)
                    ds = floored(s_up) - floored(s)
                    got = pricer.compute_gauge_delta(h, tenor, ORACLE_DE_NOTIONAL, 0.0,
                                                     ORACLE_DE_FLAT_RATE, curve)
                    basis = pricer.compute_basis_delta(h, 0.0, tenor, ORACLE_DE_NOTIONAL, 0.0,
                                                       ORACLE_DE_FLAT_RATE, curve)
                    fair = pricer.compute_prs_spread(h, tenor, 0.0, ORACLE_DE_FLAT_RATE,
                                                     yield_curve=curve)
                    mtm = pricer.compute_mark_to_market(ORACLE_DE_TRADE_SPREAD_BPS, fair,
                                                        got["risky_annuity"], ORACLE_DE_NOTIONAL)
                    exact = {"delta_spread_bps": ds,
                             "dv01_gbp": ds / ORACLE_PRS_BPS * ann * ORACLE_DE_NOTIONAL,
                             "risky_annuity": ann,
                             "mtm": (floored(s) - mp.mpf(ORACLE_DE_TRADE_SPREAD_BPS))
                             / ORACLE_PRS_BPS * ann * ORACLE_DE_NOTIONAL}
                    model = {**got, "mtm": mtm}
                    rows.append({
                        "id": f"{name}/T={tenor}/h={h!r}", "curve": name, "T": tenor, "h": h,
                        "annuity_model": repr(pricer.compute_risky_annuity(
                            h, tenor, ORACLE_DE_FLAT_RATE, curve)),
                        "annuity_ref": mp.nstr(ann, 30),
                        "annuity_rel_err": rel_err(pricer.compute_risky_annuity(
                            h, tenor, ORACLE_DE_FLAT_RATE, curve), ann),
                        **{f"{k}_model": model[k] for k in exact},
                        **{f"{k}_ref": mp.nstr(v, 25) for k, v in exact.items()},
                        **{f"{k}_err": float(abs(mp.mpf(model[k]) - v)) for k, v in exact.items()},
                        "basis_equals_gauge": basis["basis_delta_bps"] == got["delta_spread_bps"],
                        "floored": bool(s < MIN_PRS_SPREAD_BPS),
                        "gradient_bp": mp.nstr(grad, 25),
                        "fd_minus_gradient_bp": float(s_up - s - grad),
                    })
    return rows


def _wl_rate(curve, shift=0):
    sh = f" + {wl_precise(shift)}" if shift else ""
    if not curve:
        return f"Function[t, {wl_precise(ORACLE_DE_FLAT_RATE)}{sh}]"
    knots = sorted((int(k), wl_precise(v)) for k, v in curve.items())
    pieces = [f"{{{knots[0][1]}{sh}, t <= {knots[0][0]}}}"]
    pieces += [f"{{{ra} + ({rb} - {ra}) (t - {a})/{b - a}{sh}, t <= {b}}}"
               for (a, ra), (b, rb) in zip(knots, knots[1:])]
    return f"Function[t, Piecewise[{{{', '.join(pieces)}}}, {knots[-1][1]}{sh}]]"


def wl_spread(curve, tenor, shift=0):
    """s(x) in bp and A(x) as Wolfram Functions of the annual rate x (exact sums)."""
    k, n = ORACLE_PRS_PERIODS_PER_YEAR, ORACLE_PRS_PERIODS_PER_YEAR * tenor
    rr = _wl_rate(curve, shift)
    ann = f"Sum[Exp[Log[1 - x] i/{k}] Exp[-{rr}[i/{k}] i/{k}]/{k}, {{i, 1, {n}}}]"
    prot = (f"Sum[(Exp[Log[1 - x] (i - 1)/{k}] - Exp[Log[1 - x] i/{k}]) "
            f"Exp[-{rr}[(2 i - 1)/{2 * k}] (2 i - 1)/{2 * k}], {{i, 1, {n}}}]")
    return f"Function[x, {ORACLE_PRS_BPS} {prot}/{ann}]", f"Function[x, {ann}]"


def wl_items(rows):
    """Annuity, the floored forward difference, and the exact gradient, per case."""
    d, floor, bump = ORACLE_WOLFRAM_DIGITS, wl_precise(MIN_PRS_SPREAD_BPS), wl_precise(BUMP_1BP)
    # The bumped rate is the double h + 1bp, as the engine computes it -- not the
    # exact sum of two doubles, which differs by an ulp and moves a 1 bp
    # difference in the 13th digit.
    items = []
    for r in rows:
        sp, an = wl_spread(CURVES[r["curve"]], r["T"])
        h = wl_precise(r["h"])
        items += [
            (f"{r['id']}/annuity", f"N[{an}[{h}], {d}]"),
            (f"{r['id']}/ds", f"N[Max[{sp}[{wl_precise(r['h'] + BUMP_1BP)}], {floor}] - Max[{sp}[{h}], {floor}], {d}]"),
            (f"{r['id']}/gradient", f"N[(D[{sp}[x], x] /. x -> {h}) {bump}, {d}]"),
        ]
    return items


def add_wolfram(rows, wl):
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            for key, ref in (("annuity", "annuity_ref"), ("ds", "delta_spread_bps_ref"),
                             ("gradient", None)):
                w = wl_number(wl[f"{r['id']}/{key}"])
                r[f"wolfram_{key}"] = mp.nstr(w, 25)
                r[f"wolfram_{key}_vs_ref"] = rel_err(w, r[ref] if ref else r["gradient_bp"])
    return rows
