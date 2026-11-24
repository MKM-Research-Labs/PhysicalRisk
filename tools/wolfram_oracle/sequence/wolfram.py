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

"""What Wolfram computes for SS-001, independently of the reference.

Every probability is exact, from Wolfram's own TriangularDistribution and
UniformDistribution: the default batch's type mix from Eq. 4 and Table 2; the chance a
duration exceeds Eq. 6's cap (W_P - (n - 1) g_min) / n, as one tail of the triangular law
(the reference sums the rounded law instead); the chance every storm is capped and the
chance the raw gaps overflow what the storms leave, by convolving the rounded laws; and
the chance a later storm is at least as strong as the first, by Probability over the
mixture of Eq. 13.
"""

from fractions import Fraction as Q

import mpmath as mp
from tools.wolfram_oracle._wl import rel_err, wl_exact, wl_number
from tools.wolfram_oracle.sequence import reference as ref

from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SS_CORR_PROB,
    ORACLE_SS_COUNTS,
    ORACLE_SS_DURATION,
    ORACLE_SS_GAP,
    ORACLE_SS_GAP_OF,
    ORACLE_SS_SEQ_PROB,
    ORACLE_SS_TYPE_WEIGHTS,
    ORACLE_SS_VARIATION,
    ORACLE_SS_WEIGHTS,
    ORACLE_WOLFRAM_DIGITS,
)

_D = ORACLE_WOLFRAM_DIGITS
_TYPES = ("isolated", "doublet", "cluster", "persistent")


def _q(x):
    return wl_exact(Q(x))


def _type_share(t):
    total = sum(Q(w) for w in ORACLE_SS_WEIGHTS.values())
    terms = []
    for cat, w in ORACLE_SS_WEIGHTS.items():
        p = _q(ORACLE_SS_SEQ_PROB[cat])
        share = f"(1 - {p})" if t == "isolated" else f"{p} {_q(ORACLE_SS_TYPE_WEIGHTS[cat][ref.MULTI.index(t)])}"
        terms.append(f"({_q(Q(w) / total)}) {share}")
    return f"N[{' + '.join(terms)}, {_D}]"


def _cap(cat, t, n):
    a, c, b = ORACLE_SS_DURATION[cat]
    return (f"N[With[{{k = Floor[{_q(ref.cap_of(t, n))}] + 1}}, 1 - CDF[TriangularDistribution[{{{a}, {b}}}, {c}], "
            f"k - 1/2]], {_D}]")


def _rounded(name, a, c, b, value):
    return (f"{name} = List @@@ Normal[Merge[Table[({value}) -> (CDF[TriangularDistribution[{{{a}, {b}}}, {c}], "
            f"k + 1/2] - CDF[TriangularDistribution[{{{a}, {b}}}, {c}], k - 1/2]), {{k, {a}, {b}}}], Total]];")


def _gaps(cat, t, n):
    a, c, b = ORACLE_SS_DURATION[cat]
    ga, gc, gb = ORACLE_SS_GAP[ORACLE_SS_GAP_OF[t]]
    w, cap = ref.W_P, _q(ref.cap_of(t, n))
    return (
        "Module[{conv, pd, pg, sd, sg}, "
        "conv[p_, q_] := List @@@ Normal[Merge[Flatten[Outer[(#1[[1]] + #2[[1]]) -> #1[[2]] #2[[2]] &, p, q, 1]], "
        "Total]]; "
        + _rounded("pd", a, c, b, f"Min[k, {cap}]") + " " + _rounded("pg", ga, gc, gb, "k") + " "
        f"sd = Nest[conv[#, pd] &, pd, {n - 1}]; sg = Nest[conv[#, pg] &, pg, {n - 2}]; "
        f"N[{{Total[Cases[sd, {{x_, p_}} /; x == {n} {cap} :> p]], "
        f"Total[Flatten[Outer[If[#2[[1]] > {w} - #1[[1]], #1[[2]] #2[[2]], 0] &, sd, sg, 1]]]}}, {_D}]]")


def _subsequent():
    v, pc = _q(ORACLE_SS_VARIATION), _q(ORACLE_SS_CORR_PROB)
    return (f"N[Probability[x >= y, {{x \\[Distributed] MixtureDistribution[{{{pc}, 1 - {pc}}}, "
            f"{{UniformDistribution[{{0, {v}}}], UniformDistribution[{{-{v}, 0}}]}}], "
            f"y \\[Distributed] UniformDistribution[{{-{v}, 0}}]}}], {_D}]")


def items():
    """(id, expression, reference) for every oracle."""
    out = [(f"type/{t}", _type_share(t), ref.batch(ORACLE_SS_WEIGHTS)["types"][t]) for t in _TYPES]
    for cat in ORACLE_SS_WEIGHTS:
        out += [(f"cap/{cat}/{t}/{n}", _cap(cat, t, n), ref.capped(cat, t, n))
                for t in _TYPES for n in ORACLE_SS_COUNTS[t]]
        for t in ref.MULTI:
            out += [(f"gaps/{cat}/{t}/{n}", _gaps(cat, t, n), ref.gaps(cat, t, n)) for n in ORACLE_SS_COUNTS[t]]
    return out + [("subsequent", _subsequent(), ref.subsequent_vs_first())]


def _mpf(x):
    return mp.mpf(x.numerator) / x.denominator


def judge(results):
    """Wolfram's worst disagreement with the reference."""
    worst = 0.0
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for i, _, r in items():
            got = wl_number(results[i])
            pairs = zip(got, r) if isinstance(r, tuple) else [(got, r)]
            worst = max([worst] + [rel_err(g, _mpf(x)) for g, x in pairs])
    return worst
