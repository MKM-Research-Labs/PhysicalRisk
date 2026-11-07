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

"""SS-001's v2.0 equations, implemented from the document's text.

Two halves. The exact half gives each probability the document's tables imply, in
rational arithmetic: the sequence-type mix (Eq. 4, Table 2), the chance a duration is
capped (Eq. 6), and the chance the gaps are scaled (Eq. 8) or left no room at all. The
code rounds each duration and gap to whole hours, which the document does not say; the
exact half follows the code there, so that it measures the code's law. The replay half
re-runs Eqs. 4-19 on the same random stream as the code, drawing in the code's order, so
each generated sequence can be compared number for number. Its timings are exact
rationals: a capped duration is W_P/n exactly, so "no room left for gaps" is decided
without rounding.
"""

from fractions import Fraction as Q

import mpmath as mp
import numpy as np

from config.models import (
    ORACLE_SS_BASE,
    ORACLE_SS_BETA,
    ORACLE_SS_CORR_PROB,
    ORACLE_SS_COUNTS,
    ORACLE_SS_DRAIN_H,
    ORACLE_SS_DURATION,
    ORACLE_SS_FLOOR,
    ORACLE_SS_GAP,
    ORACLE_SS_GAP_OF,
    ORACLE_SS_REDRAW_PROB,
    ORACLE_SS_SEQ_PROB,
    ORACLE_SS_TYPE_WEIGHTS,
    ORACLE_SS_VARIATION,
    ORACLE_SS_WINDOW_H,
)

W_P = ORACLE_SS_WINDOW_H - ORACLE_SS_DRAIN_H          # Eq. 2
MULTI = ("doublet", "cluster", "persistent")


# --- the exact half ----------------------------------------------------------------

def _tri_cdf(x, a, c, b):
    if x <= a:
        return Q(0)
    if x >= b:
        return Q(1)
    if x <= c:
        return (x - a) ** 2 / Q((b - a) * (c - a))
    return 1 - (b - x) ** 2 / Q((b - a) * (b - c))


def rounded(a, c, b):
    """{k: P(round(D) = k)} for D ~ Triangular(a, c, b) on integer bounds."""
    half = Q(1, 2)
    return {k: _tri_cdf(k + half, a, c, b) - _tri_cdf(k - half, a, c, b) for k in range(a, b + 1)}


def convolve(p, q):
    out = {}
    for x, px in p.items():
        for y, qy in q.items():
            out[x + y] = out.get(x + y, 0) + px * qy
    return out


def power(p, n):
    out = {0: Q(1)}
    for _ in range(n):
        out = convolve(out, p)
    return out


def type_law(cat):
    """{(type, n): probability} for one category (Eq. 4, Table 2, Table 1)."""
    p = Q(ORACLE_SS_SEQ_PROB[cat])
    out = {("isolated", 1): 1 - p}
    for t, w in zip(MULTI, ORACLE_SS_TYPE_WEIGHTS[cat]):
        ns = ORACLE_SS_COUNTS[t]
        for n in ns:
            out[(t, n)] = p * Q(w) / len(ns)
    return out


def capped(cat, n):
    """Eq. 6: P(the rounded duration exceeds W_P / n)."""
    cap = Q(W_P, n)
    return sum((pk for k, pk in rounded(*ORACLE_SS_DURATION[cat]).items() if k > cap), Q(0))


def gaps(cat, t, n):
    """(P(no room for gaps: the durations fill W_P), P(the raw gaps are scaled, Eq. 8))."""
    cap = Q(W_P, n)
    d = {}
    for k, pk in rounded(*ORACLE_SS_DURATION[cat]).items():
        d[min(Q(k), cap)] = d.get(min(Q(k), cap), 0) + pk
    sd = power(d, n)
    sg = power(rounded(*ORACLE_SS_GAP[ORACLE_SS_GAP_OF[t]]), n - 1)
    zero = sd.get(Q(W_P), Q(0))
    scaled = sum((ps * pg for s, ps in sd.items() if s < W_P for g, pg in sg.items() if g > W_P - s), Q(0))
    return zero, scaled


def subsequent_vs_first():
    """P(F_i >= F_1) above the floor (Eqs. 12-13): delta_i >= delta_0."""
    pc = Q(ORACLE_SS_CORR_PROB)
    return pc + (1 - pc) * Q(1, 2)


def batch(weights):
    """The default batch's exact composition: type shares, storm-count shares, the share of
    duration draws capped, and the shares of multi-storm sequences with no gap at all and
    with gaps shorter than drawn (scaled, or no room)."""
    total = sum(Q(w) for w in weights.values())
    types, counts = {}, {}
    draws = cap_draws = multi = zero = squeezed = Q(0)
    for cat, w in weights.items():
        wc = Q(w) / total
        for (t, n), p in type_law(cat).items():
            pr = wc * p
            types[t] = types.get(t, 0) + pr
            counts[n] = counts.get(n, 0) + pr
            draws += pr * n
            cap_draws += pr * n * capped(cat, n)
            if n > 1:
                z, s = gaps(cat, t, n)
                multi += pr
                zero += pr * z
                squeezed += pr * (z + s)
    return {"types": types, "counts": counts, "cap_share": cap_draws / draws, "zero_share": zero / multi,
            "compressed_share": squeezed / multi}


def compressed(weights, cats, t):
    """P(the gaps are scaled or left no room | type t, category in cats), batch-weighted."""
    num = den = Q(0)
    for cat in cats:
        for (tt, n), p in type_law(cat).items():
            if tt == t:
                z, s = gaps(cat, t, n)
                num += Q(weights[cat]) * p * (z + s)
                den += Q(weights[cat]) * p
    return num / den


# --- the replay half -----------------------------------------------------------------

def _sequence(rng, cat, f0, force):
    v, cats = float(ORACLE_SS_VARIATION), ("doublet", "cluster", "persistent")
    if force is not None:
        t = force
    elif rng.random() < float(ORACLE_SS_SEQ_PROB[cat]):
        t = cats[rng.choice(3, p=[float(w) for w in ORACLE_SS_TYPE_WEIGHTS[cat]])]
    else:
        t = "isolated"
    ns = ORACLE_SS_COUNTS[t]
    n = ns[0] if len(ns) == 1 else int(rng.choice(list(ns)))
    cap = Q(W_P, n)                                                             # Eq. 6
    d, f = [], []
    for i in range(n):
        d.append(min(Q(round(rng.triangular(*ORACLE_SS_DURATION[cat]))), cap))  # Eqs. 5-6
        if i == 0:                                                              # Eq. 12
            delta = rng.uniform(-v, 0.0)
            if rng.random() >= ORACLE_SS_REDRAW_PROB:
                delta = rng.uniform(-v, 0.0)
        else:                                                                   # Eq. 13
            delta = rng.uniform(0.0, v) if rng.random() < float(ORACLE_SS_CORR_PROB) else rng.uniform(-v, 0.0)
        f.append(max(mp.mpf(ORACLE_SS_FLOOR), mp.mpf(f0) * (1 + mp.mpf(delta))))
    r = W_P - sum(d)
    g = [Q(0)] * (n - 1)
    if n > 1 and r > 0:
        raw = [Q(round(rng.triangular(*ORACLE_SS_GAP[ORACLE_SS_GAP_OF[t]]))) for _ in range(n - 1)]
        g = [x * r / sum(raw) for x in raw] if sum(raw) > r else raw          # Eqs. 7-8
    starts = [Q(0)]
    for i in range(1, n):                                                       # Eqs. 9-10
        starts.append(starts[-1] + d[i - 1] + g[i - 1])
    peaks = [rng.beta(*ORACLE_SS_BETA) for _ in range(n)]                       # Eq. 15
    return {"type": t, "n": n, "d": d, "g": g, "start": starts, "f": f, "peak": peaks,
            "f_max": max(f), "f_avg": sum(f) / n, "f_cum": sum(f),             # Eqs. 17-19
            "total": sum(d) + sum(g, Q(0))}                                     # Eq. 20


def with_precip(s, pbase):
    p = [mp.mpf(pbase) * x for x in s["f"]]                                     # Eq. 14
    return {**s, "p": p, "p_total": sum(p), "drain": ORACLE_SS_WINDOW_H - s["total"]}  # Eqs. 16, 3


def replay_batch(count, seed, weights, pbase, force=None):
    """generate_event_set's sequences, from the document's equations."""
    cats = list(weights)
    raw = np.array([float(weights[c]) for c in cats])
    outer, inner = np.random.RandomState(seed), np.random.RandomState(seed)
    draws = outer.choice(len(cats), size=count, p=raw / raw.sum())
    out = []
    for k in draws:
        mean, sd = ORACLE_SS_BASE[cats[k]]
        f0 = max(ORACLE_SS_FLOOR, outer.normal(mean, sd))                       # Eq. 11
        out.append(with_precip(_sequence(inner, cats[k], f0, force), pbase))
    return out


def replay_forced(rng, cat, f0, force, pbase):
    return with_precip(_sequence(rng, cat, f0, force), pbase)
