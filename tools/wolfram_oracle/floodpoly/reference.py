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
"""FPO-001's model, from its document, at 50 digits.

P = sigma(z), z = sum_k c_k h^i t^j over the document's terms, h = ln max(w/s, eps),
t = ln((hour + 1)/T), and z clamped to +/-30 before the logistic -- written from the
document's equations and printed coefficients, not from the code or its config.
"""

import mpmath as mp

from config.models import (
    ORACLE_FPO_DOC_CLAMP,
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_EPS,
    ORACLE_FPO_DOC_HOURS,
    ORACLE_FPO_DOC_TERMS,
)


def features(w, hour, s):
    """(h, t) of the document's feature equations."""
    h = mp.log(max(mp.mpf(w) / mp.mpf(s), mp.mpf(ORACLE_FPO_DOC_EPS)))
    t = mp.log(mp.mpf(hour + 1) / ORACLE_FPO_DOC_HOURS)
    return h, t


def kernel(h, t):
    return mp.fsum(mp.mpf(c) * h ** i * t ** j for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS))


def kernel_dh(h, t):
    """dz/dh, term by term."""
    return mp.fsum(mp.mpf(c) * i * h ** (i - 1) * t ** j
                   for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS) if i)


def sigma(z):
    z = max(-ORACLE_FPO_DOC_CLAMP, min(ORACLE_FPO_DOC_CLAMP, z))
    return 1 / (1 + mp.exp(-z))


def p_flood(w, hour, s):
    """The document's P(flood); zero for a non-positive threshold."""
    if s <= 0:
        return mp.mpf(0)
    return sigma(kernel(*features(w, hour, s)))


def slope(h, t):
    """dP/dh = sigma'(z) dz/dh (unclamped z)."""
    p = sigma(kernel(h, t))
    return p * (1 - p) * kernel_dh(h, t)


def p_simple(w, s):
    """s5.2: the ratio w/s capped at 1."""
    return mp.mpf(0) if s <= 0 else min(mp.mpf(1), mp.mpf(w) / mp.mpf(s))


def half_levels(hour, lo=mp.mpf("-1.5")):
    """Every w/s at which P = 1/2 at an hour, below severe: the real roots of the
    kernel as a polynomial in h, between ``lo`` and 0, ascending."""
    t = mp.log(mp.mpf(hour + 1) / ORACLE_FPO_DOC_HOURS)
    deg = max(i for i, _ in ORACLE_FPO_DOC_TERMS)
    by_power = [mp.mpf(0)] * (deg + 1)
    for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS):
        by_power[i] += mp.mpf(c) * t ** j
    while len(by_power) > 1 and by_power[-1] == 0:
        by_power.pop()
    roots = mp.polyroots(by_power[::-1], maxsteps=200, extraprec=200) if len(by_power) > 1 else []
    real = [mp.re(r) for r in roots if abs(mp.im(r)) < mp.mpf(10) ** (-mp.mp.dps // 2)]
    return sorted(mp.exp(h) for h in real if lo <= h <= 0)
