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
"""What Wolfram computes for FPO-001, independently of the reference.

From each printed coefficient, knot and input as an exact rational: P at every cell
of the document's probability table below severe, with the hour held at the envelope
by Wolfram's own Piecewise; dP/dh at a fixed hour by symbolic differentiation; and,
by NMinimize, the smallest rate of rise dz/dh over the levels each whole hour runs free
at (the model's hours are whole, Eq. 2), and along each segment of the envelope, where
the hour is held.
"""

from fractions import Fraction

import mpmath as mp
import numpy as np

from config.models import (
    ORACLE_FPO_DOC_CLAMP,
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_ENVELOPE,
    ORACLE_FPO_DOC_FLOOR,
    ORACLE_FPO_DOC_HOURS,
    ORACLE_FPO_DOC_TERMS,
    ORACLE_FPO_SLOPE_POINTS,
    ORACLE_FPO_T_HOURS,
    ORACLE_FPO_T_LEVELS,
    ORACLE_FPO_T_SEVERE,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.floodpoly import reference as ref

_D = ORACLE_WOLFRAM_DIGITS
_AGREE = mp.mpf(10) ** -20                    # the minima: Wolfram's value against the reference's at its point


def _q(x):
    f = Fraction(str(x))
    return f"({f.numerator}/{f.denominator})"


def _z(h, t):
    """The kernel, omitting zero powers."""
    term = lambda c, i, j: " ".join([_q(c)] + [f"({h})^{i}"] * bool(i) + [f"({t})^{j}"] * bool(j))
    return " + ".join(term(c, i, j) for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS))


def _dz(h, t, var):
    return f"D[{_z('hh', 'tt')}, {var}] /. {{hh -> {h}, tt -> {t}}}"


def _t(hour):
    return f"Log[({_q(hour)} + 1)/{ORACLE_FPO_DOC_HOURS}]"


def _knots():
    return [(f"Log[{_q(r)}]", _t(hr)) for r, hr in ORACLE_FPO_DOC_ENVELOPE]


def _tau(h):
    """The envelope as a Piecewise in h."""
    k = _knots()
    pieces = [f"{{-Infinity, {h} <= {k[0][0]}}}"] + [
        f"{{{t0} + ({h} - {h0})/({h1} - {h0}) ({t1} - {t0}), {h} <= {h1}}}" for (h0, t0), (h1, t1) in zip(k, k[1:])]
    return f"Piecewise[{{{', '.join(pieces)}}}, {k[-1][1]}]"


def _p(h, t, clamp=True):
    z = _z(h, f"Max[{t}, {_tau(h)}]")
    c = ORACLE_FPO_DOC_CLAMP
    return f"1/(1 + Exp[-Clip[{z}, {{-{c}, {c}}}]])" if clamp else f"1/(1 + Exp[-({z})])"


def _top(n):
    """The highest level hour n runs free at: the envelope inverted, by Wolfram, from the knots."""
    k, t = _knots(), _t(n)
    pieces = [f"{{{k[0][0]}, {t} <= {k[0][1]}}}"] + [
        f"{{{h0} + ({t} - {t0})/({t1} - {t0}) ({h1} - {h0}), {t} <= {t1}}}" for (h0, t0), (h1, t1) in zip(k, k[1:])]
    return f"Piecewise[{{{', '.join(pieces)}}}, 0]"


def regions():
    """(id, hour, constraint on h) for each whole hour: the levels from the floor up to
    the highest the hour is not held at."""
    floor = f"Log[{_q(ORACLE_FPO_DOC_FLOOR)}]"
    return [(f"free/{n}", n, f"{floor} <= h <= {_top(n)}") for n in range(ORACLE_FPO_DOC_HOURS)]


def items():
    """(id, expression, reference); the reference is None for a minimum."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return _items()


def _items():
    out, s = [], ORACLE_FPO_T_SEVERE
    for lv in ORACLE_FPO_T_LEVELS:
        for hr in ORACLE_FPO_T_HOURS:
            if lv < 1:
                out.append((f"p/{lv}/{hr}", f"N[{_p(f'Log[Max[{_q(lv)}, {_q(ORACLE_FPO_DOC_FLOOR)}]]', _t(hr))}, {_D}]",
                            ref.p_flood(mp.mpf(str(lv)) * mp.mpf(str(s)), hr, mp.mpf(str(s)))))
    for lv, hr in ORACLE_FPO_SLOPE_POINTS:
        out.append((f"slope/{lv}/{hr}", f"N[D[{_p('h', _t(hr), clamp=False)}, h] /. h -> Log[{_q(lv)}], {_D}]",
                    ref.slope(mp.log(mp.mpf(str(lv))), ref.log_time(hr))))
    for rid, n, cons in regions():
        out.append((f"min/{rid}", f"With[{{r = NMinimize[{{{_dz('h', _t(n), 'hh')}, {cons}}}, h, "
                                  f"WorkingPrecision -> {2 * _D}]}}, N[{{r[[1]], h /. r[[2]], {_t(n)}}}, {_D}]]", None))
    k = _knots()
    for a, ((h0, t0), (h1, t1)) in enumerate(zip(k, k[1:]), 1):
        h, t = f"({h0} + f ({h1} - {h0}))", f"({t0} + f ({t1} - {t0}))"
        rate = f"({_dz(h, t, 'hh')}) + ({_dz(h, t, 'tt')}) ({t1} - {t0})/({h1} - {h0})"
        out.append((f"min/env/{a}", f"With[{{r = NMinimize[{{{rate}, 0 <= f <= 1}}, f, WorkingPrecision -> {2 * _D}]}}, "
                                    f"N[{{r[[1]], {h} /. r[[2]], {t} /. r[[2]]}}, {_D}]]", None))
    return out


def _rate(rid, h, t):
    """The reference's rate of rise in a region at (h, t): dz/dh, or along the envelope."""
    if rid.startswith("env/"):
        (h0, t0), (h1, t1) = ref.knots()[int(rid.split("/")[-1]) - 1:][:2]
        return ref.kernel_dh(h, t) + ref.kernel_dt(h, t) * (t1 - t0) / (h1 - h0)    # the segment's, at its ends too
    return ref.kernel_dh(h, t)


def dense_minimum(rid, n=400):
    """The reference's smallest rate of rise in a region, on a dense grid in double
    precision: (value, h, t)."""
    k = [(float(h), float(t)) for h, t in ref.knots()]
    a = int(rid.split("/")[-1])
    c = [float(x) for x in ORACLE_FPO_DOC_COEFFS]
    dzdh = lambda h, t: sum(ci * i * h ** max(i - 1, 0) * t ** j for (i, j), ci in zip(ORACLE_FPO_DOC_TERMS, c) if i)
    dzdt = lambda h, t: sum(ci * j * h ** i * t ** max(j - 1, 0) for (i, j), ci in zip(ORACLE_FPO_DOC_TERMS, c) if j)
    f = np.linspace(0, 1, n)
    if rid.startswith("env/"):
        (h0, t0), (h1, t1) = k[a - 1], k[a]
        H, T = h0 + f * (h1 - h0), t0 + f * (t1 - t0)
        rate = dzdh(H, T) + dzdt(H, T) * (t1 - t0) / (h1 - h0)
    else:
        t = np.log((a + 1) / ORACLE_FPO_DOC_HOURS)
        hh, tt = np.array([x for x, _ in k]), np.array([y for _, y in k])
        top = 0.0 if t >= tt[-1] else float(np.interp(t, tt, hh))      # the highest level this hour runs free at
        H = np.log(float(ORACLE_FPO_DOC_FLOOR)) + np.linspace(0, 1, n * n) * (top - np.log(float(ORACLE_FPO_DOC_FLOOR)))
        T = np.full_like(H, t)
        rate = dzdh(H, T)
    i = int(np.argmin(rate))
    return float(rate[i]), float(H[i]), float(T[i])


def judge(results):
    """Wolfram's worst disagreement with the reference, and its minima by region."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        its = items()
        worst = max(rel_err(wl_number(results[i]), r) for i, _, r in its if r is not None)
        minima = {}
        for i, _, r in its:
            if r is None:
                rid = i[len("min/"):]
                v, h, t = wl_number(results[i])
                agree = abs(v - _rate(rid, h, t))
                found = dense_minimum(rid)[0] >= float(v) - 1e-9          # a global minimum, not a local one
                worst = max(worst, 1.0 if agree > _AGREE else 0.0,
                            0.0 if found else 1.0)
                minima[rid] = float(v)
    return float(worst), minima
