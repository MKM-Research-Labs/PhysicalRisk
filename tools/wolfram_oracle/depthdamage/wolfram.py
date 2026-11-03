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
"""What Wolfram computes for DD-001, independently of the reference.

Eq. 1 through Wolfram's own first-order Interpolation of Table 1; Manning and the
attenuation from exact inputs; the great-circle distance as R times the angle
between the two points' unit vectors (not the haversine); the expected clipped
shock of Eq. 11 by Expectation; the least-squares fit of the code's degree-5 curve
to Table 1, exactly; and the true east-west length of 0.1 degree at 51.5N on WGS84.
"""

from fractions import Fraction

import mpmath as mp

from config.damage import DD_POLY_COEFFS
from config.models import (
    ORACLE_DD_EARTH_R_M,
    ORACLE_DD_LATITUDE,
    ORACLE_DD_SHOCK,
    ORACLE_DD_TABLE5_DEPTHS,
    ORACLE_DD_TABLE6,
    ORACLE_DD_TABLE7,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_number, wl_precise
from tools.wolfram_oracle.depthdamage import reference as ref
from tools.wolfram_oracle.depthdamage.cases import POINTS

DELTAS = ("0.05", "0.3", "0.6", "0.9", "1")
_D = ORACLE_WOLFRAM_DIGITS


def _q(x):
    """A printed decimal as an exact Wolfram rational."""
    f = Fraction(str(x))
    return f"({f.numerator}/{f.denominator})"


def _table1():
    return "{" + ", ".join(f"{{{_q(d)}, {_q(v)}}}" for d, v in ref.TABLE1_TEXT) + "}"


def _unit(lat, lon):
    p, l = (f"{wl_precise(x)} Pi/180" for x in (lat, lon))
    return f"{{Cos[{p}] Cos[{l}], Cos[{p}] Sin[{l}], Sin[{p}]}}"


def items():
    """(id, expression, reference) for every numerical oracle; the reference is None
    where Wolfram's answer is itself the finding."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return _items()


def _items():
    out = []
    for d in ORACLE_DD_TABLE5_DEPTHS:
        out.append((f"dd/{d}", f"N[Interpolation[{_table1()}, InterpolationOrder -> 1][{_q(d)}], {_D}]",
                    ref.damage(mp.mpf(str(d)))))
    t6 = ORACLE_DD_TABLE6
    for n in t6["n"]:
        for h in t6["depths"]:
            out.append((f"manning/{n}/{h}", f"N[{wl_precise(h)}^(2/3) Sqrt[{wl_precise(t6['slope'])}]/{wl_precise(n)}, {_D}]",
                        ref.manning(h, t6["slope"], n)))
    for d in ORACLE_DD_TABLE7["distances"]:
        for ell in ORACLE_DD_TABLE7["lengths"]:
            out.append((f"att/{d}/{ell}", f"N[Exp[-{d}/{ell}], {_D}]", ref.attenuation(d, ell)))
    for i, (a, b, c, e) in enumerate(POINTS):
        out.append((f"sphere/{i}", f"N[{ORACLE_DD_EARTH_R_M} VectorAngle[{_unit(a, b)}, {_unit(c, e)}], {_D}]",
                    ref.haversine(a, b, c, e)))
    for dl in DELTAS:
        out.append((f"clip/{dl}", f"N[Expectation[Clip[{_q(dl)} (1 + {_q(ORACLE_DD_SHOCK)} z), {{0, 1}}], "
                                  f"z \\[Distributed] NormalDistribution[]], {_D}]",
                    ref.expected_clipped(mp.mpf(dl))))
    xs = [d for d, _ in ref.TABLE1_TEXT]
    out.append(("poly/ls", f"N[LeastSquares[Table[x^k, {{x, {{{', '.join(_q(x) for x in xs)}}}}}, {{k, 1, 5}}], "
                           f"{_table1()}[[All, 2]]], {_D}]", None))
    out.append(("ew/0.1", f"N[QuantityMagnitude[GeoDistance[GeoPosition[{{{_q(ORACLE_DD_LATITUDE)}, 0}}], "
                          f"GeoPosition[{{{_q(ORACLE_DD_LATITUDE)}, 1/10}}]], \"Meters\"], {_D}]", None))
    return out


def judge(results):
    """Wolfram's worst disagreement with the reference, the largest gap between the
    code's curve coefficients and the exact least-squares fit, and the true length of
    0.1 degree east-west at the Thames latitude."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        worst = max(rel_err(wl_number(results[i]), r) for i, _, r in items() if r is not None)
        ls = wl_number(results["poly/ls"])
        coeff_gap = max(abs(mp.mpf(c) - x) for c, x in zip(DD_POLY_COEFFS, ls))
        ew = wl_number(results["ew/0.1"])
    return float(worst), float(coeff_gap), float(ew)
