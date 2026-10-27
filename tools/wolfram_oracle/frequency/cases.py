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

"""EF-001's frequency maths: the model's own code vs a 50-digit reference and Wolfram.

The reference implements the document (``event_frequency_plan.pdf`` v2.3), not the
code:

* annualisation, Eq. 2: P = 1 - exp(-lambda p), aggregate lambda p, return period
  1/(lambda p);
* the tenor, s5.11: P(T) = 1 - exp(-p sum_y lambda_y) for a stationary or
  geometrically trending rate;
* the compound-Poisson year loss, s5.9: mean lambda sum(w L), variance
  lambda sum(w L^2), and the standard error of an n-year mean;
* family selection, s5.4: the chi-square dispersion test on (n-1) s^2/xbar, the
  Poisson log-likelihood, and the Negative Binomial maximum likelihood.
"""

import mpmath as mp
import numpy as np

from config.models import (
    ORACLE_EF_CATALOGUES,
    ORACLE_EF_COUNT_SERIES,
    ORACLE_EF_LAMBDAS,
    ORACLE_EF_LOSS_YEARS,
    ORACLE_EF_P_EVENTS,
    ORACLE_EF_ROOT,
    ORACLE_EF_SEED,
    ORACLE_EF_SOURCES,
    ORACLE_EF_TENORS,
    ORACLE_EF_TERM_SOURCE,
    ORACLE_EF_TREND,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._model import load_module
from tools.wolfram_oracle._wl import rel_err, wl_list, wl_precise


def load():
    mods = {k: load_module(v, ORACLE_EF_ROOT) for k, v in ORACLE_EF_SOURCES.items()}
    mods["term"] = load_module(ORACLE_EF_TERM_SOURCE)
    return mods


def _row(group, rid, model, ref, **extra):
    return {"id": f"{group}/{rid}", "group": group, "model": repr(float(model)),
            "ref": mp.nstr(ref, 30), "rel_err": rel_err(model, ref), **extra}


def annualisation(m):
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for lam in ORACLE_EF_LAMBDAS:
            for p in ORACLE_EF_P_EVENTS:
                x = mp.mpf(lam) * mp.mpf(p)
                rows.append(_row("annual", f"lam={lam!r},p={p!r}",
                                 m["annualise"].annual_exceedance_probability(lam, p), -mp.expm1(-x),
                                 lam=lam, p=p))
                rows.append(_row("rate", f"lam={lam!r},p={p!r}",
                                 m["annualise"].annual_exceedance_rate(lam, p), x, lam=lam, p=p))
    return rows


def _rates(base, growth, tenor):
    return [mp.mpf(base) * (1 + mp.mpf(growth)) ** y for y in range(tenor)]


def term(m):
    """Exact tenor probability: the model's, its term structure's (v2.4, s5.10),
    and v2.3's convention -- the annual probabilities compounded -- beside them."""
    rows, rp = [], m["rate_process"]
    base, growth = ORACLE_EF_TREND
    cases = [("const", lam, 0.0) for lam in (2.0, 10.0)] + [("trend", base, growth)]
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for kind, lam, g in cases:
            process = rp.rate_process_for(lam, g)
            for p in (0.001, 0.01, 0.05):
                for t in ORACLE_EF_TENORS:
                    exact = -mp.expm1(-mp.mpf(p) * mp.fsum(_rates(lam, g, t)))
                    hazards = m["annualise"].annual_hazard_by_year(process, p, t)
                    structure = m["term"].compute_term_structure(hazards, t)[-1].prob_at_least_one
                    v23 = -mp.expm1(-mp.fsum(-mp.expm1(-mp.mpf(p) * r) for r in _rates(lam, g, t)))
                    rows.append(_row("term", f"{kind},lam={lam!r},p={p!r},T={t}",
                                     rp.term_exceedance_probability(process, p, t), exact,
                                     lam=lam, growth=g, p=p, T=t,
                                     structure=repr(float(structure)),
                                     structure_rel_err=rel_err(structure, exact),
                                     v23=mp.nstr(v23, 30), v23_gap=float(v23 / exact - 1)))
    return rows


def catalogues():
    rng = np.random.default_rng(ORACLE_EF_SEED)
    out = []
    for k, lam in ORACLE_EF_CATALOGUES:
        w = rng.dirichlet(np.ones(k))
        loss = np.round(rng.lognormal(0.0, 1.0, k) * (rng.random(k) < 0.4), 6)
        out.append((f"K={k},lam={lam!r}", lam, w, loss))
    return out


def compound(m):
    rows, rec = [], m["reconcile"]
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for rid, lam, w, loss in catalogues():
            ws, ls = [mp.mpf(float(v)) for v in w], [mp.mpf(float(v)) for v in loss]
            mean = mp.mpf(lam) * mp.fsum(a * b for a, b in zip(ws, ls))
            second = mp.mpf(lam) * mp.fsum(a * b * b for a, b in zip(ws, ls))
            rows.append(_row("aal", rid, rec.analytic_average_annual_loss(lam, w, loss), mean,
                             lam=lam, w=[float(v) for v in w], loss=[float(v) for v in loss]))
            rows.append(_row("aal_se", rid, rec.loss_standard_error(lam, w, loss, ORACLE_EF_LOSS_YEARS),
                             mp.sqrt(second / ORACLE_EF_LOSS_YEARS), lam=lam,
                             w=[float(v) for v in w], loss=[float(v) for v in loss]))
    return rows


def count_series():
    rng = np.random.default_rng(ORACLE_EF_SEED + 1)
    out = []
    for kind, n, args in ORACLE_EF_COUNT_SERIES:
        if kind == "poisson":
            c = rng.poisson(args[0], n)
        elif kind == "negbin":
            r = 1 / args[1]
            c = rng.negative_binomial(r, r / (r + args[0]), n)
        else:
            c = rng.binomial(args[0], args[1], n)
        out.append((f"{kind}{args},n={n}", [int(v) for v in c]))
    return out


def _nb_ll(counts, mu, alpha):
    r = 1 / mp.mpf(alpha)
    return mp.fsum(mp.loggamma(k + r) - mp.loggamma(r) - mp.loggamma(k + 1)
                   + r * mp.log(r / (r + mu)) + k * mp.log(mu / (r + mu)) for k in counts)


def families(m):
    rows = []
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for rid, c in count_series():
            n, mean = len(c), mp.mpf(sum(c)) / len(c)
            var = mp.fsum((k - mean) ** 2 for k in c) / (n - 1)
            stat, dof = (n - 1) * var / mean, n - 1
            test = m["select"].dispersion_test(c, 0.05)
            p_over = mp.gammainc(mp.mpf(dof) / 2, stat / 2, regularized=True)
            pois_ll = mp.fsum(k * mp.log(mean) - mean - mp.loggamma(k + 1) for k in c)
            fit = m["negbin"].fit_negbin(c)
            alpha_star = (mp.findroot(lambda a: mp.diff(lambda b: _nb_ll(c, mean, b), a), fit.alpha)
                          if fit.alpha > 0 else mp.mpf(0))
            best = _nb_ll(c, mean, alpha_star) if alpha_star > 0 else pois_ll
            extra = {"counts": c, "regime": test.regime, "alpha_model": fit.alpha,
                     "alpha_ref": float(alpha_star)}
            rows += [
                _row("disp_stat", rid, test.statistic, stat, **extra),
                _row("p_over", rid, test.p_over, p_over, **extra),
                _row("p_under", rid, test.p_under, 1 - p_over, **extra),
                _row("pois_ll", rid, m["poisson"].fit_poisson(c).log_likelihood, pois_ll, **extra),
                {**_row("nb_ll", rid, fit.log_likelihood, best, **extra),
                 "ll_gap": float(best - mp.mpf(fit.log_likelihood))},
            ]
    return rows


def _wl_counts(c):
    return "{" + ", ".join(str(k) for k in c) + "}"


def wl_items(rows):
    """Each case as Wolfram computes it from the document's definitions."""
    d, items = ORACLE_WOLFRAM_DIGITS, []
    for r in rows:
        g, rid = r["group"], r["id"]
        if g in ("annual", "rate"):
            lam, p = wl_precise(r["lam"]), wl_precise(r["p"])
            items.append((rid, f"N[1 - Exp[-{lam} {p}], {d}]" if g == "annual" else f"N[{lam} {p}, {d}]"))
        elif g == "term":
            lam, gr, p = wl_precise(r["lam"]), wl_precise(r["growth"]), wl_precise(r["p"])
            items.append((rid, f"N[1 - Exp[-{p} Sum[{lam} (1 + {gr})^y, {{y, 0, {r['T'] - 1}}}]], {d}]"))
        elif g in ("aal", "aal_se"):
            # EmpiricalDistribution renormalises the weights; the catalogue's sum to one
            # only in floating point, so the rate is rescaled by their exact total.
            w = wl_list(r["w"], wl_precise)
            dist = (f"CompoundPoissonDistribution[{wl_precise(r['lam'])} Total[{w}], "
                    f"EmpiricalDistribution[{w} -> {wl_list(r['loss'], wl_precise)}]]")
            expr = (f"Mean[{dist}]" if g == "aal"
                    else f"Sqrt[Variance[{dist}]/{ORACLE_EF_LOSS_YEARS}]")
            items.append((rid, f"N[{expr}, {d}]"))
        else:
            c = _wl_counts(r["counts"])
            n = len(r["counts"])
            stat = f"(({n} - 1) Variance[{c}]/Mean[{c}])"
            expr = {
                "disp_stat": f"N[{stat}, {d}]",
                "p_over": f"N[SurvivalFunction[ChiSquareDistribution[{n - 1}], {stat}], {d}]",
                "p_under": f"N[CDF[ChiSquareDistribution[{n - 1}], {stat}], {d}]",
                "pois_ll": f"N[LogLikelihood[PoissonDistribution[Mean[{c}]], {c}], {d}]",
            }.get(g)
            if g == "nb_ll":
                # Wolfram's own likelihood, maximised jointly over (r, q); under-dispersed
                # data has its supremum in the Poisson limit, r -> infinity.
                expr = (f"Module[{{f}}, f[t_?NumericQ, u_?NumericQ] := LogLikelihood["
                        f"NegativeBinomialDistribution[Exp[t], LogisticSigmoid[u]], {c}]; "
                        f"N[Max[First[Quiet[FindMaximum[f[t, u], {{t, 0}}, {{u, -Log[Mean[{c}]]}}, "
                        f"WorkingPrecision -> {d}]]], LogLikelihood[PoissonDistribution[Mean[{c}]], {c}]], {d}]]")
            items.append((rid, expr))
    return items
