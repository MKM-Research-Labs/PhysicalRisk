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

"""Per-gauge evaluation: held-out accuracy, then the stability tests.

Accuracy: GroupKFold over real storms.  Every fold trains on its training
storms plus all near-miss vectors and scores on its held-out real storms only,
giving one out-of-fold prediction per real row per model.  Tunable models get
the same random-search budget, scored on an inner storm split.

Stability (on fold 0's training storms, scored on fold 0's held-out storms and
on the probability-surface grid): seed refits, storm bootstraps, and the shape
of the fold-0 surface (monotonicity in water level, roughness).

Every fit is an independent job; jobs run in three parallel batches (tuning,
fold fits, stability) so all cores stay busy.
"""

import time

import numpy as np
from joblib import Parallel, delayed
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from config.models import (
    CHALLENGER_GRID_HOUR_STEP,
    CHALLENGER_GRID_LEVEL_POINTS,
    CHALLENGER_GRID_LEVEL_QUANTILES,
    CHALLENGER_INNER_HOLDOUT,
    CHALLENGER_MONOTONE_TOL,
    CHALLENGER_SEARCH_SPACE,
)
from config.port import LOG_END, NUM_CLASSIFIER_HOURS

from ._candidates import CANDIDATES, make_model
from ._metrics import brier, score


def _fit_predict(name, params, seed, X, y, groups, evals):
    """One job: fit a candidate, return its predictions on each of ``evals``."""
    model = make_model(name, params, seed).fit(X, y, groups)
    return [model.predict(E) for E in evals]


def _run_jobs(jobs, n_jobs):
    """Run ``(name, params, seed, X, y, groups, evals)`` jobs; results in order."""
    return Parallel(n_jobs=n_jobs)(delayed(_fit_predict)(*job) for job in jobs)


def _sample_params(space, rng):
    return {k: v[rng.randint(len(v))] for k, v in space.items()}


def _inner_split(groups, seed):
    """Inner tuning split: hold back real storms; near-miss stays in training."""
    real = groups >= 0
    split = GroupShuffleSplit(n_splits=1, test_size=CHALLENGER_INNER_HOLDOUT,
                              random_state=seed)
    real_idx = np.flatnonzero(real)
    fit_r, val_r = next(split.split(real_idx, groups=groups[real]))
    return np.concatenate([real_idx[fit_r], np.flatnonzero(~real)]), real_idx[val_r]


def _trials(space_name, trials, seed):
    """Trial 0 is the model's defaults; the rest are random draws."""
    rng = np.random.RandomState(seed)
    space = CHALLENGER_SEARCH_SPACE[space_name]
    return [{}] + [_sample_params(space, rng) for _ in range(max(trials - 1, 0))]


def surface_grid(X_real):
    """Grid over (log_h_s, log_t_end) with Δ = Δ² = 0: the probability surface."""
    lo, hi = np.quantile(X_real[:, 0], CHALLENGER_GRID_LEVEL_QUANTILES)
    levels = np.linspace(lo, hi, CHALLENGER_GRID_LEVEL_POINTS)
    hours = np.arange(0, NUM_CLASSIFIER_HOURS, CHALLENGER_GRID_HOUR_STEP)
    times = np.log((hours + 1) / LOG_END)
    hh, tt = np.meshgrid(levels, times, indexing="ij")
    grid = np.column_stack([hh.ravel(), tt.ravel(), np.zeros(hh.size), np.zeros(hh.size)])
    return grid, levels, hours


def shape_metrics(p_grid, n_levels):
    """Monotonicity violations in water level and roughness of the surface.

    ``p_grid`` is laid out level-major (as :func:`surface_grid`).  A violation is
    a fall of more than the tolerance between adjacent levels at a fixed hour.
    Roughness is the mean |second difference| along the level axis.
    """
    surf = p_grid.reshape(n_levels, -1)
    d1 = np.diff(surf, axis=0)
    d2 = np.diff(surf, n=2, axis=0)
    return {
        "monotone_violations": int((d1 < -CHALLENGER_MONOTONE_TOL).sum()),
        "monotone_violation_rate": float((d1 < -CHALLENGER_MONOTONE_TOL).mean()),
        "max_fall": float(max(0.0, -d1.min())),
        "roughness": float(np.abs(d2).mean()),
    }


def _bootstrap_rows(groups_real, train_real_idx, rng):
    """Rows of a storm bootstrap of ``train_real_idx``, with fresh group ids."""
    storms = np.unique(groups_real[train_real_idx])
    by_storm = {s: train_real_idx[groups_real[train_real_idx] == s] for s in storms}
    draw = rng.choice(storms, len(storms), replace=True)
    rows = [by_storm[s] for s in draw]
    new_groups = np.concatenate([np.full(len(r), k) for k, r in enumerate(rows)])
    return np.concatenate(rows), new_groups


def _sd(preds):
    sd = np.array(preds).std(0)
    return float(sd.mean()), float(sd.max())


def evaluate_gauge(gs, folds, trials, seeds, bootstraps, seed, log=print, n_jobs=-1):
    """Score every candidate on one gauge.  Returns a JSON-ready dict plus the
    per-storm out-of-fold Brier scores used for paired statistics."""
    t0 = time.time()
    n_real, n_total = gs.n_real, len(gs.y)
    Xr, yr, gr = gs.X[:n_real], gs.y[:n_real], gs.groups[:n_real]
    nm = np.arange(n_real, n_total)
    n_storms = len(np.unique(gr))
    if n_storms < folds or not 0 < yr.sum() < n_real:
        return {"gauge_id": gs.gauge_id, "status": "skipped",
                "reason": "too few storms or single-class labels",
                "n_storms": int(n_storms), "n_positive": int(yr.sum())}

    names = list(CANDIDATES)
    splits = list(GroupKFold(n_splits=folds).split(Xr, yr, gr))
    train = [np.concatenate([tr, nm]) for tr, _ in splits]

    # ---- batch 1: tuning trials, every fold × tunable model --------------
    jobs, keys = [], []
    for k, rows in enumerate(train):
        X, y, g = gs.X[rows], gs.y[rows], gs.groups[rows]
        fit_i, val_i = _inner_split(g, seed + k)
        for name, spec in CANDIDATES.items():
            if not spec["tune"]:
                continue
            for params in _trials(spec["tune"], trials, seed + k):
                jobs.append((name, params, seed, X[fit_i], y[fit_i], g[fit_i], [X[val_i]]))
                keys.append((k, name, params, y[val_i]))
    best = {}
    for (k, name, params, y_val), (p,) in zip(keys, _run_jobs(jobs, n_jobs)):
        s = brier(y_val, p)
        if (k, name) not in best or s < best[(k, name)][1]:
            best[(k, name)] = (params, s)
    fold_params = {n: [] for n in names}
    for k in range(folds):
        for name, spec in CANDIDATES.items():
            if spec["tune"]:
                params = best[(k, name)][0]
            else:
                src = spec.get("params_from")
                params = dict(fold_params[src][k]) if src else {}
            fold_params[name].append(params)
    log(f"    tuning: {len(jobs)} fits  [{time.time() - t0:.0f}s]")

    # ---- batch 2: fold fits -> out-of-fold predictions and fold-0 surface --
    grid, levels, hours = surface_grid(Xr)
    jobs, keys = [], []
    for k, ((_, te), rows) in enumerate(zip(splits, train)):
        for name in names:
            evals = [Xr[te], grid] if k == 0 else [Xr[te]]
            jobs.append((name, fold_params[name][k], seed,
                         gs.X[rows], gs.y[rows], gs.groups[rows], evals))
            keys.append((k, name, te))
    oof = {n: np.full(n_real, np.nan) for n in names}
    surface = {}
    for (k, name, te), preds in zip(keys, _run_jobs(jobs, n_jobs)):
        oof[name][te] = preds[0]
        if k == 0:
            surface[name] = preds[1]
    log(f"    fold fits: {len(jobs)} fits  [{time.time() - t0:.0f}s]")

    accuracy = {n: score(yr, oof[n]) for n in names}
    _, inverse = np.unique(gr, return_inverse=True)
    storm_brier = {n: np.bincount(inverse, (oof[n] - yr) ** 2) / np.bincount(inverse)
                   for n in names}

    # ---- batch 3: stability on fold 0 (seed refits, storm bootstraps) -----
    tr0, te0 = splits[0]
    rows0 = train[0]
    fit_names = [n for n in names if not CANDIDATES[n].get("fixed")]
    jobs, keys = [], []
    for name in fit_names:
        if not CANDIDATES[name]["stochastic"]:
            continue
        for s in range(seeds):
            jobs.append((name, fold_params[name][0], seed + 1 + s,
                         gs.X[rows0], gs.y[rows0], gs.groups[rows0], [grid, Xr[te0]]))
            keys.append(("seed", name))
    rng = np.random.RandomState(seed)
    for _ in range(bootstraps):
        rows_b, groups_b = _bootstrap_rows(gr, tr0, rng)
        X = np.vstack([Xr[rows_b], gs.X[nm]])
        y = np.concatenate([yr[rows_b], gs.y[nm]])
        g = np.concatenate([groups_b, gs.groups[nm]])
        for name in fit_names:
            jobs.append((name, fold_params[name][0], seed, X, y, g, [grid, Xr[te0]]))
            keys.append(("bootstrap", name))
    runs = {}
    for key, preds in zip(keys, _run_jobs(jobs, n_jobs)):
        runs.setdefault(key, []).append(preds)
    log(f"    stability: {len(jobs)} fits  [{time.time() - t0:.0f}s]")

    stability = {}
    for name in names:
        entry = {"shape": shape_metrics(surface[name], len(levels)),
                 "surface": surface[name].round(5).tolist()}
        if name in fit_names:
            seed_runs = runs.get(("seed", name))
            if seed_runs:
                g_mean, g_max = _sd([r[0] for r in seed_runs])
                h_mean, _ = _sd([r[1] for r in seed_runs])
                entry["seed"] = {"grid_sd_mean": g_mean, "grid_sd_max": g_max,
                                 "heldout_sd_mean": h_mean,
                                 "mean_p_sd": float(np.std([r[1].mean() for r in seed_runs]))}
            else:
                entry["seed"] = {"grid_sd_mean": 0.0, "grid_sd_max": 0.0,
                                 "heldout_sd_mean": 0.0, "mean_p_sd": 0.0}
            boot_runs = runs.get(("bootstrap", name), [])
            if boot_runs:
                g_mean, g_max = _sd([r[0] for r in boot_runs])
                briers = [brier(yr[te0], r[1]) for r in boot_runs]
                entry["bootstrap"] = {"grid_sd_mean": g_mean, "grid_sd_max": g_max,
                                      "brier_sd": float(np.std(briers)),
                                      "brier_mean": float(np.mean(briers))}
        stability[name] = entry

    return {
        "gauge_id": gs.gauge_id,
        "status": "scored",
        "label": gs.label_name,
        "n_storms": int(n_storms),
        "n_rows": int(n_real),
        "n_nearmiss_rows": int(n_total - n_real),
        "flood_rate": float(yr.mean()),
        "accuracy": accuracy,
        "stability": stability,
        "params": fold_params,
        "grid": {"log_h_s": levels.round(5).tolist(), "hours": hours.tolist()},
        "seconds": round(time.time() - t0, 1),
        "_storm_brier": storm_brier,
        "_oof": oof,
        "_y": yr,
    }
