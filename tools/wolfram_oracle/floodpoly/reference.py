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

v2.0, s3: P = 1 at or above severe. Below it P = sigma(z(h, max(t, tau(h)))), z the
sum of c_k h^i t^j over the printed terms and coefficients, h = ln max(w/s, floor),
t = ln((hour + 1)/T), tau the support envelope through the printed knots (linear in t
between them, -inf below the first), z clamped to +/-30 before the logistic -- written
from the document's equations and tables, not from the code or its config.
"""

import mpmath as mp

from config.models import (
    ORACLE_FPO_DOC_CLAMP,
    ORACLE_FPO_DOC_COEFFS,
    ORACLE_FPO_DOC_ENVELOPE,
    ORACLE_FPO_DOC_FLOOR,
    ORACLE_FPO_DOC_HOURS,
    ORACLE_FPO_DOC_TERMS,
)


def log_time(hour):
    return mp.log(mp.mpf(hour + 1) / ORACLE_FPO_DOC_HOURS)


def knots():
    """The envelope's knots as (h, t)."""
    return [(mp.log(mp.mpf(r)), log_time(mp.mpf(hr))) for r, hr in ORACLE_FPO_DOC_ENVELOPE]


def tau(h):
    """The earliest supported t at level h; -inf below the first knot."""
    k = knots()
    if h <= k[0][0]:
        return -mp.inf
    for (h0, t0), (h1, t1) in zip(k, k[1:]):
        if h <= h1:
            return t0 + (h - h0) / (h1 - h0) * (t1 - t0)
    return k[-1][1]


def tau_slope(h):
    k = knots()
    for (h0, t0), (h1, t1) in zip(k, k[1:]):
        if h0 < h < h1:
            return (t1 - t0) / (h1 - h0)
    return mp.mpf(0)


def features(w, hour, s):
    """(h, t) of the document's feature equations, before the hold."""
    return mp.log(max(mp.mpf(w) / mp.mpf(s), mp.mpf(ORACLE_FPO_DOC_FLOOR))), log_time(hour)


def kernel(h, t):
    return mp.fsum(mp.mpf(c) * h ** i * t ** j for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS))


def kernel_dh(h, t):
    return mp.fsum(mp.mpf(c) * i * h ** (i - 1) * t ** j
                   for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS) if i)


def kernel_dt(h, t):
    return mp.fsum(mp.mpf(c) * j * h ** i * t ** (j - 1)
                   for (i, j), c in zip(ORACLE_FPO_DOC_TERMS, ORACLE_FPO_DOC_COEFFS) if j)


def sigma(z):
    z = max(-ORACLE_FPO_DOC_CLAMP, min(ORACLE_FPO_DOC_CLAMP, z))
    return 1 / (1 + mp.exp(-z))


def p_features(h, t):
    """P at log level h and log time t: 1 at or above severe, else held and fitted."""
    if h >= 0:
        return mp.mpf(1)
    h = max(h, mp.log(mp.mpf(ORACLE_FPO_DOC_FLOOR)))
    return sigma(kernel(h, max(t, tau(h))))


def p_flood(w, hour, s):
    """The document's P(flood); zero for a non-positive threshold."""
    if s <= 0:
        return mp.mpf(0)
    return mp.mpf(1) if mp.mpf(w) >= mp.mpf(s) else p_features(*features(w, hour, s))


def held(w, hour, s):
    """Whether the hour is held at the envelope (the document's dagger)."""
    h, t = features(w, hour, s)
    return mp.mpf(w) < mp.mpf(s) and t < tau(h)


def slope(h, t):
    """dP/dh at a fixed hour (s3.4): along the envelope where the hour is held there."""
    if h >= 0 or h < mp.log(mp.mpf(ORACLE_FPO_DOC_FLOOR)):
        return mp.mpf(0)
    te = tau(h)
    if t < te:
        t, dz = te, kernel_dh(h, te) + kernel_dt(h, te) * tau_slope(h)
    else:
        dz = kernel_dh(h, t)
    p = sigma(kernel(h, t))
    return p * (1 - p) * dz


def p_simple(w, s):
    """s6.3: the ratio w/s capped at 1."""
    return mp.mpf(0) if s <= 0 else min(mp.mpf(1), mp.mpf(w) / mp.mpf(s))
