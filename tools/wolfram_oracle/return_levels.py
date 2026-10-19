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

"""Return levels and exceedance: GH-001's own code vs a 50-digit closed form and Wolfram.

Convention: GEV with shape xi in the EVT sign (xi > 0 Frechet / heavy tail).
    F(x) = exp(-(1 + xi*(x - mu)/sigma)^(-1/xi)),  xi != 0
    F(x) = exp(-exp(-(x - mu)/sigma)),            xi == 0

GEVFitter takes return levels as ppf(1 - p) and exceedance as 1 - cdf, and
switches to Gumbel below |xi| < 1e-10; each of those is exercised here. The
exceedance threshold is the exact T-year level, so the right answer is 1/T.
"""

import mpmath as mp
from scipy.stats import genextreme

from config.models import (
    ORACLE_GEV_CASES,
    ORACLE_OPERATING_MAX_T,
    ORACLE_REFERENCE_DPS,
    ORACLE_RETURN_PERIODS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_exact, wl_gev, wl_number


def return_level_ref(mu, sigma, xi, T):
    """Exact return level: x_T = F^-1(1 - 1/T)."""
    mu, sigma, xi = mp.mpf(mu), mp.mpf(sigma), mp.mpf(xi)
    y = -mp.log(1 - 1 / mp.mpf(T))  # reduced variate, precise for large T
    if xi == 0:
        return mu - sigma * mp.log(y)
    return mu + sigma / xi * mp.expm1(-xi * mp.log(y))


def exceedance_ref(mu, sigma, xi, x):
    """Exact P(X > x), without forming 1 - F."""
    mu, sigma, xi, x = (mp.mpf(v) for v in (mu, sigma, xi, x))
    if xi == 0:
        return -mp.expm1(-mp.exp(-(x - mu) / sigma))
    return -mp.expm1(-(1 + xi * (x - mu) / sigma) ** (-1 / xi))


def run(gev_fitter, cases=ORACLE_GEV_CASES, periods=ORACLE_RETURN_PERIODS):
    fitter = gev_fitter()
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for name, (mu, sigma, xi) in cases.items():
            for T in periods:
                level = return_level_ref(mu, sigma, xi, T)
                x = float(level)  # the threshold the model is handed
                exc = exceedance_ref(mu, sigma, xi, x)
                got_level = float(fitter.return_level(T, xi, mu, sigma))
                got_exc = float(fitter.exceedance_probability(x, xi, mu, sigma))
                rows.append({
                    "id": f"{name}/T={T}", "case": name, "mu": mu, "sigma": sigma,
                    "xi": xi, "T": T, "threshold": x,
                    "level_ref": mp.nstr(level, 30), "level_model": repr(got_level),
                    "level_rel_err": rel_err(got_level, level),
                    "exc_ref": mp.nstr(exc, 30), "exc_model": repr(got_exc),
                    "exc_rel_err": rel_err(got_exc, exc),
                })
    return rows


def wl_items(rows):
    d = ORACLE_WOLFRAM_DIGITS
    items = []
    for r in rows:
        dist = wl_gev(r["mu"], r["sigma"], r["xi"])
        items.append((r["id"] + "/level", f"N[Quantile[{dist}, 1 - 1/{r['T']}], {d}]"))
        items.append((r["id"] + "/exc",
                      f"N[SurvivalFunction[{dist}, {wl_exact(r['threshold'])}], {d}]"))
    return items


def add_wolfram(rows, wl):
    """Annotate each row with Wolfram's value and both comparisons."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            for kind in ("level", "exc"):
                w = wl_number(wl[f"{r['id']}/{kind}"])
                r[f"{kind}_wolfram"] = mp.nstr(w, 30)
                r[f"{kind}_wolfram_vs_ref"] = rel_err(w, r[f"{kind}_ref"])
                r[f"{kind}_model_vs_wolfram"] = rel_err(r[f"{kind}_model"], w)
    return rows


def worst(rows, key, max_t=ORACLE_OPERATING_MAX_T):
    """The row with the largest ``key`` inside the operating range."""
    return max((r for r in rows if r["T"] <= max_t), key=lambda r: r[key])


def sign_trap(mu=100.0, sigma=20.0, xi=0.2, T=1000):
    """What scipy returns if xi goes in unflipped — what _flip_convention prevents."""
    return {"correct (c = -xi)": float(genextreme.isf(1 / T, -xi, loc=mu, scale=sigma)),
            "unflipped (c = +xi)": float(genextreme.isf(1 / T, xi, loc=mu, scale=sigma))}
