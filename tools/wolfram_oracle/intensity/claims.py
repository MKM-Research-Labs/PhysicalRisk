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

"""SI-001's model document and code comments, tested as stated, scenario by scenario.

* s3.4 -- the composite exceedance is continuous at the threshold u (proved there);
* the code's own docstring -- "the Pareto scale is calibrated so the PDF is
  continuous at the threshold" -- which the document does not claim;
* s3.5 / s5.3 -- Acklam's inverse normal is accurate to about 1.15e-9, absolute;
* s8.4 -- clamping to [Imin, Imax] is "a slight probability mass distortion";
* s3.6 -- the return-period intensity S^-1(1/(T lambda)), and the T from which
  the clamp makes it Imax whatever T is;
* s5.4 / s8.5 -- the sampling jitter does not materially affect the moments.

The moments are exact: E[Q(U)] and E[Q(U)^2] by quadrature over p, and with the
jitter, E[clamp(Q(U) + e)] with the Gaussian integral over e done in closed form.
"""

import math

import mpmath as mp

from config.models import (
    ORACLE_SI_CLAIM_ACKLAM,
    ORACLE_SI_CLAIM_JITTER_REL,
    ORACLE_SI_CLAIM_SLIGHT_MASS,
    ORACLE_SI_JITTER_SD,
    ORACLE_SI_STORMS_PER_YEAR,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import wl_precise
from tools.wolfram_oracle.intensity.distribution import (
    _wl_sf,
    cap_masses,
    params,
    quantile_ref,
    tail_prob,
)

MOMENT_DPS = 30  # quadrature of an erfinv-based integrand; 30 digits is ample


def _breakpoints(p):
    """Where Q(p) has kinks: the Imax plateau, the branch switch, the Imin plateau."""
    m_min, m_max = cap_masses(p)
    return [mp.mpf(0), m_max, tail_prob(p), 1 - m_min, mp.mpf(1)]


def _clamped_jitter(y, lo, hi, tau, power):
    """E[clamp(y + e, lo, hi)^power] for e ~ N(0, tau^2), power 1 or 2, in closed form."""
    a, b = (lo - y) / tau, (hi - y) / tau
    inside = mp.ncdf(b) - mp.ncdf(a)
    if power == 1:
        mid = y * inside + tau * (mp.npdf(a) - mp.npdf(b))
    else:
        mid = (y * y * inside + 2 * y * tau * (mp.npdf(a) - mp.npdf(b))
               + tau * tau * (inside + a * mp.npdf(a) - b * mp.npdf(b)))
    return lo ** power * mp.ncdf(a) + hi ** power * (1 - mp.ncdf(b)) + mid


def moments(p):
    """(mean, sd) of Q(U), and of clamp(Q(U) + jitter), exactly."""
    with mp.workdps(MOMENT_DPS):
        _, _, _, _, lo, hi = params(p)
        tau, pts = mp.mpf(ORACLE_SI_JITTER_SD), _breakpoints(p)
        q = lambda v: quantile_ref(p, v)  # noqa: E731
        m1, m2 = mp.quad(q, pts), mp.quad(lambda v: q(v) ** 2, pts)
        j1 = mp.quad(lambda v: _clamped_jitter(q(v), lo, hi, tau, 1), pts)
        j2 = mp.quad(lambda v: _clamped_jitter(q(v), lo, hi, tau, 2), pts)
        return (m1, mp.sqrt(m2 - m1 ** 2)), (j1, mp.sqrt(j2 - j1 ** 2))


def by_scenario(dist_cls, families):
    """One row per scenario: tail, clamp masses, density jump, cap T, moments."""
    out = []
    for name, p in families.items():
        mu, s, u, a, _, _ = params(p)
        m_min, m_max = cap_masses(p)
        d = dist_cls(params=p)
        (mean, sd), (jmean, jsd) = moments(p)
        out.append({
            "scenario": name, "p_tail": float(tail_prob(p)),
            "mass_min": float(m_min), "mass_max": float(m_max),
            "pdf_ratio": float((tail_prob(p) * a / u) / (mp.npdf((u - mu) / s) / s)),
            "s_jump": abs(d.exceedance_probability(p.tail_threshold)
                          - d.exceedance_probability(math.nextafter(p.tail_threshold, math.inf))),
            "cap_T": float(1 / (ORACLE_SI_STORMS_PER_YEAR * m_max)),
            "mean": float(mean), "sd": float(sd),
            "jitter_mean_rel": float(jmean / mean - 1), "jitter_sd_rel": float(jsd / sd - 1),
        })
    return out


def assess(scenarios, ack_rows):
    """Each claim as {claim, ..., met} -- met is None for a finding."""
    ack = max(r["abs_err"] for r in ack_rows)
    ack_rel = max(r["rel_err"] for r in ack_rows)
    worst_max = max(scenarios, key=lambda r: r["mass_max"])
    jitter = max(max(abs(r["jitter_mean_rel"]), abs(r["jitter_sd_rel"])) for r in scenarios)
    ratios = [r["pdf_ratio"] for r in scenarios]
    return [
        {"claim": "s3.4 continuity of S at u", "worst": max(r["s_jump"] for r in scenarios),
         "met": max(r["s_jump"] for r in scenarios) < 1e-12},
        {"claim": "code: PDF continuous at u", "low": min(ratios), "high": max(ratios),
         "met": False if any(abs(x - 1) > 1e-6 for x in ratios) else True},
        {"claim": "s3.5/s5.3 Acklam accuracy", "worst": ack, "relative": ack_rel,
         "limit": ORACLE_SI_CLAIM_ACKLAM, "met": ack <= ORACLE_SI_CLAIM_ACKLAM},
        {"claim": "s8.4 slight mass at the clamp", "worst": worst_max["mass_max"],
         "at": worst_max["scenario"], "limit": ORACLE_SI_CLAIM_SLIGHT_MASS,
         "met": worst_max["mass_max"] <= ORACLE_SI_CLAIM_SLIGHT_MASS},
        {"claim": "s3.6 return periods reach Imax", "worst": min(r["cap_T"] for r in scenarios),
         "high": max(r["cap_T"] for r in scenarios), "met": None},
        {"claim": "s5.4/s8.5 jitter on moments", "worst": jitter, "limit": ORACLE_SI_CLAIM_JITTER_REL,
         "met": jitter <= ORACLE_SI_CLAIM_JITTER_REL},
    ]


def wl_moment_items(families):
    """E[Q(U)] and E[Q(U)^2] per scenario, by Wolfram's NIntegrate over p."""
    items = []
    for name, p in families.items():
        mu, s, u, a = (wl_precise(v) for v in (p.base_mean, p.base_std, p.tail_threshold, p.tail_index))
        lo, hi = wl_precise(p.min_intensity), wl_precise(p.max_intensity)
        pts = ", ".join(wl_precise(float(v)) if 0 < v < 1 else str(int(v)) for v in _breakpoints(p))
        q = (f"Clip[Piecewise[{{{{{u} (pt/v)^(1/{a}), v < pt}}}}, "
             f"{mu} + {s} InverseCDF[NormalDistribution[0, 1], 1 - v]], {{{lo}, {hi}}}]")
        head = f"Module[{{pt = {_wl_sf(p, u)}}}, "
        for k, power in (("m1", ""), ("m2", "^2")):
            items.append((f"{name}/{k}", f"{head}NIntegrate[({q}){power}, {{v, {pts}}}, "
                          f"WorkingPrecision -> {ORACLE_WOLFRAM_DIGITS + 10}]]"))
    return items
