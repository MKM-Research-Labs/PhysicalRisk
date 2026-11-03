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
"""The v2.0 fit: the kernel that best reproduces the GBMs where production uses it.

The polynomial sees the level ratio and the hour; each gauge's GBM (MKM-FC-001) also
sees the rate of rise. So the target is the GBM's probability on the real storm
states the classifiers are trained on, below severe -- at and above it a flood has
happened and P = 1 -- pooled over every gauge so one kernel serves them all, as
production applies it. States near severe weigh more, because stress P&L is decided
there. Half the storms fit; the other half measure.

The kernel is constrained to rise with the level from the level floor up to severe:
a penalty on any negative dz/dh over a grid of levels and hours, which the fit drives
to zero. Below the floor the model holds its value there, as it is fitted. Earlier
than the support envelope it holds the hour there, so the same penalty also holds the
rate of change along the envelope, dz/dh + dz/dt dt/dh, positive.
"""

import numpy as np
from scipy.optimize import least_squares

from config.models import (
    flood_poly_envelope,
    flood_poly_fit_envelope_points,
    flood_poly_fit_grid,
    flood_poly_fit_max_evals,
    flood_poly_fit_near,
    flood_poly_fit_near_weight,
    flood_poly_fit_penalty,
    flood_poly_fit_seed,
    flood_poly_fit_slope_margin,
    flood_poly_fit_storms,
    flood_poly_fit_tol,
    flood_poly_level_floor,
    flood_poly_storm_hours,
    flood_poly_terms,
)


def design(h, t, terms=flood_poly_terms):
    return np.column_stack([h ** i * t ** j for i, j in terms])


def design_dh(h, t, terms=flood_poly_terms):
    return np.column_stack([i * h ** max(i - 1, 0) * t ** j if i else np.zeros_like(h) for i, j in terms])


def design_dt(h, t, terms=flood_poly_terms):
    return np.column_stack([j * h ** i * t ** max(j - 1, 0) if j else np.zeros_like(h) for i, j in terms])


def _envelope_knots():
    hh = np.log([r for r, _ in flood_poly_envelope])
    tt = np.log((np.array([hour for _, hour in flood_poly_envelope]) + 1) / flood_poly_storm_hours)
    return hh, tt


def held_t(h, t):
    """t held at the support envelope, as the model holds it."""
    hh, tt = _envelope_knots()
    return np.maximum(t, np.interp(h, hh, tt, left=-np.inf))


def envelope_rows(n=flood_poly_fit_envelope_points):
    """d(kernel)/dh along each envelope segment, the hour moving with the level."""
    hh, tt = _envelope_knots()
    rows = []
    for a in range(len(hh) - 1):
        f = np.linspace(0, 1, n)
        h, t = hh[a] + f * (hh[a + 1] - hh[a]), tt[a] + f * (tt[a + 1] - tt[a])
        rows.append(design_dh(h, t) + (tt[a + 1] - tt[a]) / (hh[a + 1] - hh[a]) * design_dt(h, t))
    return np.vstack(rows)


def _sigma(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def states(n_storms=flood_poly_fit_storms, seed=flood_poly_fit_seed):
    """Pooled (h, t, gbm, gauge, storm, fit?) over every gauge with a classifier, below severe."""
    from tools.wolfram_oracle.floodpoly import gbm
    from tools.flood_classifier_challenger._data import load_catalogue
    rows, rng = [], np.random.RandomState(seed)
    for k, gs in enumerate(load_catalogue(gbm.gauge_ids(), n_storms=n_storms, seed=seed)):
        X, grp = gs.X[:gs.n_real], gs.groups[:gs.n_real]
        g = gbm.classifier(gs.gauge_id).predict_proba(X)[:, 1]
        keep = X[:, 0] < 0
        storms = np.unique(grp)
        fit = np.isin(grp, rng.choice(storms, len(storms) // 2, replace=False))
        h = np.maximum(X[keep, 0], np.log(flood_poly_level_floor))   # the model's level floor
        rows.append((h, X[keep, 1], g[keep], np.full(keep.sum(), k), fit[keep]))
    return tuple(np.concatenate(c) for c in zip(*rows))


def fit(h, t, g):
    """Weighted least squares of sigma(kernel) to the GBM, with the monotone penalty."""
    w = np.sqrt(np.where(h >= np.log(flood_poly_fit_near), flood_poly_fit_near_weight, 1.0))
    lo, n = flood_poly_fit_grid
    gh, gt = np.meshgrid(np.linspace(np.log(lo), 0, n),
                         np.log((np.arange(flood_poly_storm_hours) + 1) / flood_poly_storm_hours))
    gh, gt = gh.ravel(), gt.ravel()
    F, Fg = design(h, held_t(h, t)), np.vstack([design_dh(gh, gt), envelope_rows()])
    lam = np.sqrt(flood_poly_fit_penalty)

    def resid(c):
        return np.concatenate([w * (_sigma(F @ c) - g), lam * np.minimum(Fg @ c - flood_poly_fit_slope_margin, 0)])

    def jac(c):
        s = _sigma(F @ c)
        J1 = (w * s * (1 - s))[:, None] * F
        J2 = lam * (Fg @ c < flood_poly_fit_slope_margin)[:, None] * Fg
        return np.vstack([J1, J2])

    tol = flood_poly_fit_tol
    res = least_squares(resid, np.zeros(F.shape[1]), jac=jac, method="trf", x_scale="jac",
                        ftol=tol, xtol=tol, gtol=tol, max_nfev=flood_poly_fit_max_evals)
    return res.x, float((Fg @ res.x).min())


def metrics(c, h, t, g, gauge, near=flood_poly_fit_near):
    """Per gauge on held-out storms: mean |P - GBM| near severe and below it."""
    p = _sigma(design(h, held_t(h, t)) @ c)
    out = []
    for k in np.unique(gauge):
        m = gauge == k
        nm = m & (h >= np.log(near))
        out.append({"gauge": int(k), "near_mae": float(np.abs(p - g)[nm].mean()),
                    "near_bias": float((p - g)[nm].mean()), "near_over": float((np.abs(p - g)[nm] > 0.1).mean()),
                    "below_mae": float(np.abs(p - g)[m].mean())})
    return out
