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

From each printed coefficient and input as an exact rational: the clamped logistic
at every cell of the document's Table 1; the level at which P = 1/2, by solving the
kernel for its real roots below severe; and dP/dh by symbolic differentiation.
"""

from fractions import Fraction

import mpmath as mp

from config.models import (
    ORACLE_FPO_CONTOUR_HOURS,
    ORACLE_FPO_DOC_CLAMP,
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_HOURS,
    ORACLE_FPO_DOC_TERMS,
    ORACLE_FPO_T1_HOURS,
    ORACLE_FPO_T1_LEVELS,
    ORACLE_FPO_T1_SEVERE,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.floodpoly import reference as ref

_D = ORACLE_WOLFRAM_DIGITS
SLOPE_RATIO = "0.9"


def _q(x):
    f = Fraction(str(x))
    return f"({f.numerator}/{f.denominator})"


def _z(h, t):
    """The kernel, omitting zero powers (t is exactly 0 at the final hour)."""
    term = lambda c, i, j: " ".join([_q(c)] + [f"{h}^{i}"] * bool(i) + [f"{t}^{j}"] * bool(j))
    return " + ".join(term(c, i, j) for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS))


def _t(hour):
    return f"Log[{hour + 1}/{ORACLE_FPO_DOC_HOURS}]"


def items():
    """(id, expression, reference); the reference is None for a set of roots."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return _items()


def _items():
    out, s, c = [], ORACLE_FPO_T1_SEVERE, ORACLE_FPO_DOC_CLAMP
    for w in ORACLE_FPO_T1_LEVELS:
        for hr in ORACLE_FPO_T1_HOURS:
            z = _z(f"Log[{_q(w)}/{_q(s)}]", _t(hr))
            out.append((f"p/{w}/{hr}", f"N[1/(1 + Exp[-Clip[{z}, {{-{c}, {c}}}]]), {_D}]",
                        ref.p_flood(mp.mpf(str(w)), hr, mp.mpf(str(s)))))
    for hr in ORACLE_FPO_CONTOUR_HOURS:
        out.append((f"half/{hr}", f"N[Table[Exp[h] /. r, {{r, NSolve[{_z('h', _t(hr))} == 0 && -3/2 <= h <= 0, "
                                  f"h, Reals, WorkingPrecision -> {2 * _D}]}}], {_D}]", None))
        h0 = f"Log[{_q(SLOPE_RATIO)}]"
        out.append((f"slope/{hr}", f"N[D[1/(1 + Exp[-({_z('h', _t(hr))})]), h] /. h -> {h0}, {_D}]",
                    ref.slope(mp.log(mp.mpf(SLOPE_RATIO)), mp.log(mp.mpf(hr + 1) / ORACLE_FPO_DOC_HOURS))))
    return out


def _roots(text):
    v = wl_number(text) if text.strip() not in ("{}", "") else []
    return sorted(v) if isinstance(v, list) else [v]


def judge(results):
    """Wolfram's worst disagreement with the reference, and the P = 1/2 levels by hour."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        its = items()
        worst = max(rel_err(wl_number(results[i]), r) for i, _, r in its if r is not None)
        half = {}
        for hr in ORACLE_FPO_CONTOUR_HOURS:
            roots, mine = _roots(results[f"half/{hr}"]), ref.half_levels(hr)
            half[hr] = [float(x) for x in roots]
            if len(roots) != len(mine):
                worst = max(worst, 1.0)
            worst = max([worst] + [rel_err(x, y) for x, y in zip(roots, mine)])
    return float(worst), half
