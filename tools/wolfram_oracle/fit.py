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

"""The fit: is GH-001's maximum-likelihood fit actually the maximum?

The closed forms are the easy part. What carries the risk is the fit —
GEVFitter.fit is scipy's genextreme.fit (gumbel_r.fit when forced), a local
optimiser whose answer moves the shape xi, and xi drives every tail level.
Three views of each series:

* the model's own fit, through GH-001's GEVFitter;
* a log-likelihood written from the density (no scipy.stats), maximised from
  several starts and evaluated at 50 digits at both parameter sets;
* Wolfram: EstimatedDistribution, and LogLikelihood at the model's parameters.

A fit is suspect if another method finds a higher log-likelihood, and material
if that moves the 1-in-100 or 1-in-1000 level.
"""

import json

import mpmath as mp
import numpy as np
from scipy.optimize import minimize
from scipy.stats import genextreme

from config.models import (
    ORACLE_FIT_CHECK_T,
    ORACLE_FIT_MAX_ITER,
    ORACLE_FIT_OPT_TOL,
    ORACLE_FIT_ROUND_DP,
    ORACLE_FIT_SEED,
    ORACLE_FIT_SYNTHETIC,
    ORACLE_FIT_XI_STARTS,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_exact, wl_list, wl_machine, wl_number

EULER_GAMMA = float(mp.euler)


def synthetic_series(spec=ORACLE_FIT_SYNTHETIC, seed=ORACLE_FIT_SEED):
    rng = np.random.default_rng(seed)
    return {name: np.round(genextreme.rvs(-xi, mu, s, size=n, random_state=rng),
                           ORACLE_FIT_ROUND_DP)
            for name, (n, mu, s, xi) in spec.items()}


def load_gauges(path):
    """id -> peak levels, from a list or a PhysicalRisk gauge-timeseries record."""
    def peaks(v):
        if isinstance(v, dict):
            v = [r["peak_level_m"] for r in v["storm_responses"]["responses"]]
        return np.asarray(v, dtype=float)
    return {k: peaks(v) for k, v in json.loads(open(path).read()).items()}


def loglik_mp(x, mu, sigma, xi):
    """GEV log-likelihood at 50 digits, written from the density."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        mu, sigma, xi = mp.mpf(mu), mp.mpf(sigma), mp.mpf(xi)
        total = -len(x) * mp.log(sigma)
        for v in x:
            z = (mp.mpf(v) - mu) / sigma
            if xi == 0:
                total += -z - mp.exp(-z)
                continue
            t = 1 + xi * z
            if t <= 0:
                return -mp.inf
            total += -(1 + 1 / xi) * mp.log(t) - t ** (-1 / xi)
        return +total


def _nll(p, x, gumbel):
    mu, sigma, xi = p[0], np.exp(p[1]), (0.0 if gumbel else p[2])
    z = (x - mu) / sigma
    if xi == 0.0:
        return len(x) * np.log(sigma) + np.sum(z + np.exp(-z))
    t = 1 + xi * z
    if np.any(t <= 0):
        return np.inf
    return len(x) * np.log(sigma) + (1 + 1 / xi) * np.sum(np.log(t)) + np.sum(t ** (-1 / xi))


def independent_fit(x, gumbel=False):
    """Multi-start Nelder-Mead on the hand-written likelihood: (xi, mu, sigma)."""
    s0 = np.std(x) * np.sqrt(6) / np.pi  # Gumbel method-of-moments start
    m0 = np.mean(x) - EULER_GAMMA * s0
    best = None
    for xi0 in ((0.0,) if gumbel else ORACLE_FIT_XI_STARTS):
        p0 = [m0, np.log(s0)] + ([] if gumbel else [xi0])
        with np.errstate(invalid="ignore"):  # inf - inf while a start is off-support
            r = minimize(_nll, p0, args=(x, gumbel), method="Nelder-Mead",
                         options={"xatol": ORACLE_FIT_OPT_TOL, "fatol": ORACLE_FIT_OPT_TOL,
                                  "maxiter": ORACLE_FIT_MAX_ITER})
        if best is None or r.fun < best.fun:
            best = r
    return (0.0 if gumbel else float(best.x[2])), float(best.x[0]), float(np.exp(best.x[1]))


def run(gev_fitter, series, truth=ORACLE_FIT_SYNTHETIC):
    rows = []
    for name, x in series.items():
        for gumbel in (False, True):
            fitter = gev_fitter(force_gumbel=gumbel)
            model = tuple(float(v) for v in fitter.fit(x))  # (xi, loc, scale)
            indep = independent_fit(x, gumbel)
            ll_m = loglik_mp(x, model[1], model[2], model[0])
            ll_i = loglik_mp(x, indep[1], indep[2], indep[0])
            t = truth.get(name)
            rows.append({
                "id": f"{name}/{'gumbel' if gumbel else 'gev'}", "series": name,
                "family": "gumbel" if gumbel else "gev", "n": len(x),
                "truth_xi_loc_scale": (t[3], t[1], t[2]) if t else None,
                "model_xi_loc_scale": model, "indep_xi_loc_scale": indep,
                "ll_model": mp.nstr(ll_m, 25), "ll_indep": mp.nstr(ll_i, 25),
                "ll_gain_indep": float(ll_i - ll_m),
                "levels": {T: {"model": float(fitter.return_level(T, *model)),
                               "indep": float(fitter.return_level(T, *indep)),
                               "truth": (float(genextreme.isf(1 / T, -t[3], t[1], t[2]))
                                         if t else None)}
                           for T in ORACLE_FIT_CHECK_T},
                "x": [float(v) for v in x],
            })
    return rows


def wl_items(rows):
    d = ORACLE_WOLFRAM_DIGITS
    items = []
    for r in rows:
        xi, mu, s = r["model_xi_loc_scale"]
        if r["family"] == "gumbel":
            at_model = f"ExtremeValueDistribution[{wl_exact(mu)}, {wl_exact(s)}]"
            family, pars = "ExtremeValueDistribution[m, s]", "{0, #[[1]], #[[2]]}"
        else:
            at_model = f"MaxStableDistribution[{wl_exact(mu)}, {wl_exact(s)}, {wl_exact(xi)}]"
            family, pars = "MaxStableDistribution[m, s, x]", "{#[[3]], #[[1]], #[[2]]}"
        exact, machine = wl_list(r["x"], wl_exact), wl_list(r["x"], wl_machine)
        fit = (f"EstimatedDistribution[{machine}, {family}, "
               'ParameterEstimator -> "MaximumLikelihood"]')
        items += [
            (r["id"] + "/ll_at_model", f"N[LogLikelihood[{at_model}, {exact}], {d}]"),
            (r["id"] + "/fit_xi_loc_scale", f"{pars} &[List @@ {fit}]"),
            (r["id"] + "/ll_at_fit", f"LogLikelihood[{fit}, {machine}]"),
        ]
    return items


def add_wolfram(rows, wl):
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            ll_w = wl_number(wl[r["id"] + "/ll_at_model"])
            r["ll_wolfram_vs_mp"] = rel_err(ll_w, r["ll_model"])
            r["wolfram_xi_loc_scale"] = [float(v) for v in wl_number(wl[r["id"] + "/fit_xi_loc_scale"])]
            r["ll_gain_wolfram"] = float(wl_number(wl[r["id"] + "/ll_at_fit"]) - mp.mpf(r["ll_model"]))
    return rows
