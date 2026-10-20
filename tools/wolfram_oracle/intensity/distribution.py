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

"""SI-001's distribution: the model's own code vs a 50-digit reference and Wolfram.

The reference implements the model document (``storm_intensity.pdf`` v1.3, s3),
not the code. With mu, sigma the Normal body, u the threshold, alpha the tail
index and [Imin, Imax] the clamp:

* p_tail = S_N(u), the Normal's exceedance at u (Eq. 3.4);
* S(x) = 1 below Imin, S_N(x) up to u, p_tail (u/x)^alpha above it, 0 from Imax;
* S^-1(p) = mu + sigma Phi^-1(1 - p) for p >= p_tail, else u (p_tail/p)^(1/alpha),
  clamped to [Imin, Imax] (s3.5);
* the T-year intensity is S^-1(1/(T lambda)) with lambda storms a year (s3.6).

Phi^-1 here is exact. The model uses Acklam's approximation, which is checked on
its own -- on the same doubles the model is given, so input rounding is not
mistaken for approximation error.
"""

import mpmath as mp

from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SI_ACKLAM_BODY_STEP,
    ORACLE_SI_ACKLAM_EXPONENTS,
    ORACLE_SI_P_EXPONENTS,
    ORACLE_SI_P_MULTIPLIERS,
    ORACLE_SI_RETURN_PERIODS,
    ORACLE_SI_STORMS_PER_YEAR,
    ORACLE_SI_X_STEP,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_number, wl_precise


def params(p):
    """(mu, sigma, u, alpha, Imin, Imax) as mpf."""
    return tuple(mp.mpf(v) for v in (p.base_mean, p.base_std, p.tail_threshold,
                                     p.tail_index, p.min_intensity, p.max_intensity))


def phi_inv(q):
    return mp.sqrt(2) * mp.erfinv(2 * mp.mpf(q) - 1)


def tail_prob(p):
    mu, s, u, _, _, _ = params(p)
    return mp.ncdf(-(u - mu) / s)


def exceedance_ref(p, x):
    mu, s, u, a, lo, hi = params(p)
    x = mp.mpf(x)
    if x <= lo:
        return mp.mpf(1)
    if x >= hi:
        return mp.mpf(0)
    if x <= u:
        return mp.ncdf(-(x - mu) / s)
    return tail_prob(p) * (u / x) ** a


def quantile_ref(p, prob):
    """S^-1(p), clamped to [Imin, Imax]."""
    mu, s, u, a, lo, hi = params(p)
    prob = mp.mpf(prob)
    pt = tail_prob(p)
    x = mu + s * phi_inv(1 - prob) if prob >= pt else u * (pt / prob) ** (1 / a)
    return max(lo, min(hi, x))


def cap_masses(p):
    """The probability the clamp puts exactly on Imin and on Imax."""
    mu, s, u, a, lo, hi = params(p)
    return 1 - mp.ncdf(-(lo - mu) / s), tail_prob(p) * (u / hi) ** a


def _probabilities():
    ps = sorted({m * 10.0 ** -k for k in ORACLE_SI_P_EXPONENTS for m in ORACLE_SI_P_MULTIPLIERS})
    return ps + [1 - q for q in reversed(ps)]


def run(dist_cls, families):
    """Every case: exceedance on a grid of x, quantile on a grid of p, return periods."""
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for name, p in families.items():
            d = dist_cls(params=p)
            n = round((p.max_intensity - p.min_intensity) / ORACLE_SI_X_STEP)
            for x in (p.min_intensity + i * ORACLE_SI_X_STEP for i in range(n + 1)):
                rows.append(_row(name, "exc", x, d.exceedance_probability(x), exceedance_ref(p, x)))
            for q in _probabilities():
                rows.append(_row(name, "inv", q, d.inverse_exceedance(q), quantile_ref(p, q)))
            for t in ORACLE_SI_RETURN_PERIODS:
                q = 1 / (t * ORACLE_SI_STORMS_PER_YEAR)
                ref = quantile_ref(p, q)
                rows.append(_row(name, "rp", t, d.return_period_intensity(t, ORACLE_SI_STORMS_PER_YEAR),
                                 ref, capped=bool(ref >= p.max_intensity), prob=q))
    return rows


def _row(scenario, kind, arg, model, ref, **extra):
    return {"id": f"{scenario}/{kind}/{arg!r}", "scenario": scenario, "kind": kind, "arg": arg,
            "model": repr(float(model)), "ref": mp.nstr(ref, 30), "rel_err": rel_err(model, ref),
            **extra}


def acklam(dist_cls):
    """Acklam's inverse normal on the very doubles it is handed, both tails and the body."""
    tails = [10.0 ** -k for k in ORACLE_SI_ACKLAM_EXPONENTS]
    body = [i * ORACLE_SI_ACKLAM_BODY_STEP for i in range(1, round(1 / ORACLE_SI_ACKLAM_BODY_STEP))]
    probs = sorted(set(tails + body + [1 - t for t in tails]))
    inv = dist_cls()._inverse_normal
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for q in probs:
            ref, got = phi_inv(q), inv(q)
            rows.append({"id": f"acklam/{q!r}", "p": q, "model": repr(got), "ref": mp.nstr(ref, 30),
                         "abs_err": float(abs(mp.mpf(got) - ref)), "rel_err": rel_err(got, ref)})
    return rows


def _wl_sf(p, x):
    """The Normal body's exceedance at x, written out. Wolfram 15.0's
    SurvivalFunction[NormalDistribution[...], x] returns machine precision even
    for a 60-digit x, which would cap the oracle at 16 digits."""
    return f"Erfc[({x} - {wl_precise(p.base_mean)})/({wl_precise(p.base_std)} Sqrt[2])]/2"


def _wl_quantile(p, prob):
    mu, s, u, a = (wl_precise(v) for v in (p.base_mean, p.base_std, p.tail_threshold, p.tail_index))
    lo, hi = wl_precise(p.min_intensity), wl_precise(p.max_intensity)
    pp = wl_precise(prob)
    if mp.mpf(prob) >= tail_prob(p):
        body = f"{mu} + {s} InverseCDF[NormalDistribution[0, 1], 1 - {pp}]"
    else:
        body = f"{u} ({_wl_sf(p, u)}/{pp})^(1/{a})"
    return f"Clip[{body}, {{{lo}, {hi}}}]"


def wl_items(rows, ack_rows, families):
    """Each case as a Wolfram expression; the branch is the document's, chosen exactly."""
    d = ORACLE_WOLFRAM_DIGITS
    items = []
    for r in rows:
        p = families[r["scenario"]]
        if r["kind"] == "exc":
            x = r["arg"]
            if x <= p.min_intensity or x >= p.max_intensity:
                expr = "1" if x <= p.min_intensity else "0"
            elif x <= p.tail_threshold:
                expr = f"N[{_wl_sf(p, wl_precise(x))}, {d}]"
            else:
                u = wl_precise(p.tail_threshold)
                expr = (f"N[{_wl_sf(p, u)} ({u}/{wl_precise(x)})"
                        f"^{wl_precise(p.tail_index)}, {d}]")
        else:
            expr = f"N[{_wl_quantile(p, r['prob'] if r['kind'] == 'rp' else r['arg'])}, {d}]"
        items.append((r["id"], expr))
    items += [(r["id"], f"N[InverseCDF[NormalDistribution[0, 1], {wl_precise(r['p'])}], {d}]")
              for r in ack_rows]
    return items


def add_wolfram(rows, ack_rows, wl):
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            w = wl_number(wl[r["id"]])
            r["wolfram"] = mp.nstr(w, 30)
            r["wolfram_vs_ref"] = rel_err(w, r["ref"])
            r["model_vs_wolfram"] = rel_err(r["model"], w)
        for r in ack_rows:
            w = wl_number(wl[r["id"]])
            r["wolfram_vs_ref"] = rel_err(w, r["ref"])
            r["abs_err_vs_wolfram"] = float(abs(mp.mpf(r["model"]) - w))
    return rows, ack_rows
