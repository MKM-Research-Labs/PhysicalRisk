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

"""GHD-001's statistics, exactly, from its document (``gaugehd_synthetic.pdf`` v1.0, s3).

On a day without a flood the level is mu0 + S_t + T_t + eps_t. If the last flood was
k days earlier, it reset eps to R = W_flood - mu0, so eps_t = phi^k R plus Gaussian
noise of variance sigma_w^2 (1 - phi^(2k)); with no flood yet, the AR(1) started
from 0. The tide is A_tau M_t V with V uniform on [-1, 1] and the flood level is
uniform, so P(W_t >= h) is a double integral of a normal tail over two uniforms,
which has a closed form in G(z) = phi(z) - z Q(z) and H(z) = ((z^2+1) Q(z) - z phi(z))/2.
Summing over days and over the geometric law of k gives each expected count; the
base level mu0 = FloodAlert U(0.3, 0.5) is integrated by Gauss-Legendre.
Evaluated in double precision: the comparison is with sampling error.
"""

import math

import numpy as np
from scipy.special import erfc

from config.models import (
    ORACLE_GHD_BASE_BAND,
    ORACLE_GHD_HISTORICAL_HIGH,
    ORACLE_GHD_MAX_AGE,
    ORACLE_GHD_MINOR_RATIO,
    ORACLE_GHD_MU_NODES,
    ORACLE_GHD_PHASE_DAYS,
    ORACLE_GHD_ROUND_HALF,
    ORACLE_GHD_SEVERE_TOP,
    ORACLE_GHD_SPRING_NEAP,
    ORACLE_GHD_TABLE1,
    ORACLE_GHD_THRESHOLDS,
)

_R2 = math.sqrt(2.0)


def q_tail(z):
    return 0.5 * erfc(z / _R2)


def _pdf(z):
    return np.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def g_int(z):
    """G(z) = int_z^inf Q."""
    return _pdf(z) - z * q_tail(z)


def h_int(z):
    """H(z) = int_z^inf G."""
    return 0.5 * ((z * z + 1) * q_tail(z) - z * _pdf(z))


def tail_uniforms(alpha, beta, r1, r2, gamma):
    """E[Q(alpha - beta R - gamma V)], R ~ U(r1, r2), V ~ U(-1, 1); beta, gamma >= 0."""
    alpha, beta, gamma = np.broadcast_arrays(*(np.asarray(x, dtype=float) for x in (alpha, beta, gamma)))
    width = beta * (r2 - r1)
    mid = alpha - beta * 0.5 * (r1 + r2)
    out = np.empty(alpha.shape)
    narrow = width < 1e-6                                   # R is effectively at its mean
    tidal = gamma > 1e-12
    a, b, c = mid[narrow], gamma[narrow], tidal[narrow]
    out[narrow] = np.where(c, (g_int(a - b) - g_int(a + b)) / (2 * np.where(c, b, 1)), q_tail(a))
    w = ~narrow
    a, bt, gm, wd = alpha[w], beta[w], gamma[w], width[w]
    hi, lo = a - bt * r1, a - bt * r2                       # z at R = r1 and R = r2
    tid = gm > 1e-12
    g_safe = np.where(tid, gm, 1.0)
    out[w] = np.where(tid, (h_int(lo - g_safe) - h_int(hi - g_safe) - h_int(lo + g_safe) + h_int(hi + g_safe))
                      / (2 * g_safe * wd), (g_int(lo) - g_int(hi)) / wd)
    return out


def calendar(days_of_year):
    d = np.asarray(days_of_year)
    s = np.cos(2 * np.pi * (d - ORACLE_GHD_PHASE_DAYS) / 365)
    m = 0.6 + 0.4 * np.cos(2 * np.pi * (d % ORACLE_GHD_SPRING_NEAP) / ORACLE_GHD_SPRING_NEAP)
    return s, m


def _flood(n3, n_days_param):
    alert, warn, sev = (ORACLE_GHD_THRESHOLDS[k] for k in ("FloodAlert", "FloodWarning", "SevereFloodWarning"))
    ps = max(n3, 1) / n_days_param
    qs, qm = ps, (1 - ps) * ORACLE_GHD_MINOR_RATIO * ps
    return qs, qm, (sev, ORACLE_GHD_SEVERE_TOP * ORACLE_GHD_HISTORICAL_HIGH), (alert, warn)


def _uniform_ge(lo, hi, h):
    return min(max((hi - h) / (hi - lo), 0.0), 1.0)


def conditional(regime, n3, days_of_year, mu0, years):
    """Expected counts above each threshold and the expected level, day by day, given mu0."""
    sd, a_s, a_t, phi = ORACLE_GHD_TABLE1[regime]
    sigma, amp_s, amp_t = sd * mu0, a_s * mu0, a_t * mu0
    s_cos, m_env = calendar(days_of_year)
    n = len(days_of_year)
    qs, qm, sev, minor = _flood(n3, years * 365)
    q = qs + qm
    k = np.arange(1, ORACLE_GHD_MAX_AGE + 1)
    t = np.arange(n)
    age_w = q * (1 - q) ** (k - 1)                          # P(last flood k days ago | day t, k <= t)
    seasonal = mu0 + amp_s * s_cos
    doy, inv = np.unique(np.asarray(days_of_year), return_inverse=True)
    s_doy, m_doy = calendar(doy)
    seas_doy = mu0 + amp_s * s_doy
    # count[d, k] = number of days t with day-of-year d and t >= k (a flood k back fits)
    count = np.stack([len(t[inv == i]) - np.searchsorted(t[inv == i], k, side="left")
                      for i in range(len(doy))])
    out = {}
    for name, h in ORACLE_GHD_THRESHOLDS.items():
        h = h - ORACLE_GHD_ROUND_HALF
        p_flood = qs * _uniform_ge(*sev, h) + qm * _uniform_ge(*minor, h)
        s_k = sigma * np.sqrt(1 - phi ** (2 * k))
        alpha = (h - seas_doy[:, None]) / s_k[None, :]      # day-of-year x ages
        beta = (phi ** k / s_k)[None, :]
        gamma = amp_t * m_doy[:, None] / s_k[None, :]
        mem = (qs * tail_uniforms(alpha, beta, sev[0] - mu0, sev[1] - mu0, gamma)
               + qm * tail_uniforms(alpha, beta, minor[0] - mu0, minor[1] - mu0, gamma)) / q
        stat = tail_uniforms((h - seasonal) / sigma, 0.0, 0.0, 0.0, amp_t * m_env / sigma)
        beyond = np.clip((1 - q) ** ORACLE_GHD_MAX_AGE - (1 - q) ** t, 0, None)
        start_s = sigma * np.sqrt(1 - phi ** (2 * (t + 1)))
        start = tail_uniforms((h - seasonal) / start_s, 0.0, 0.0, 0.0, amp_t * m_env / start_s)
        non_flood = (count * age_w[None, :] * mem).sum() + (beyond * stat).sum() + ((1 - q) ** t * start).sum()
        out[name] = n * p_flood + (1 - q) * non_flood
    e_r = (qs * (0.5 * (sev[0] + sev[1]) - mu0) + qm * (0.5 * (minor[0] + minor[1]) - mu0)) / q
    memory = q * phi * (1 - ((1 - q) * phi) ** t) / (1 - (1 - q) * phi)
    flood_mean = qs * 0.5 * (sev[0] + sev[1]) + qm * 0.5 * (minor[0] + minor[1])
    out["level"] = flood_mean + (1 - q) * (seasonal + e_r * memory)
    return out


def expected(regime, n3, days_of_year, months, years):
    """The statistics' expectations, mu0 integrated over its uniform band."""
    alert = ORACLE_GHD_THRESHOLDS["FloodAlert"]
    lo, hi = (alert * b for b in ORACLE_GHD_BASE_BAND)
    x, w = np.polynomial.legendre.leggauss(ORACLE_GHD_MU_NODES)
    mus, ws = 0.5 * (hi - lo) * x + 0.5 * (hi + lo), 0.5 * w
    months = np.asarray(months)
    acc = {}
    for mu, wt in zip(mus, ws):
        c = conditional(regime, n3, days_of_year, mu, years)
        stats = {f"days_{k}": c[k] for k in ORACLE_GHD_THRESHOLDS}
        stats["mean"] = c["level"].mean()
        for mo, key in ((1, "jan_minus_mean"), (7, "jul_minus_mean")):
            stats[key] = c["level"][months == mo].mean() - c["level"].mean()
        for key, v in stats.items():
            acc[key] = acc.get(key, 0.0) + wt * v
    acc["mu0"] = 0.5 * (lo + hi)
    acc["floods"] = sum(_flood(n3, years * 365)[:2]) * len(days_of_year)
    return acc


def lag1_flood_free(regime, days_of_year):
    """The limit of the sample lag-1 autocorrelation without floods (scale-free in mu0)."""
    sd, a_s, a_t, phi = ORACLE_GHD_TABLE1[regime]
    s, m = calendar(days_of_year)
    s = a_s * (s - s.mean())
    tide = (a_t * m) ** 2 / 3
    num = (s[:-1] * s[1:]).sum() + (len(s) - 1) * phi * sd ** 2
    den = (s ** 2).sum() + len(s) * sd ** 2 + tide.sum()
    return num / den
