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

"""Pooled results, paired statistics and the pre-agreed decision rule."""

import numpy as np
from scipy.stats import wilcoxon

from config.models import (
    CHALLENGER_ALPHA,
    CHALLENGER_BRIER_TOLERANCE,
    CHALLENGER_CHAMPION,
    CHALLENGER_CI_BOOTSTRAPS,
    CHALLENGER_CI_LEVEL,
    CHALLENGER_MIN_WILCOXON_GAUGES,
    CHALLENGER_MONOTONE_RATE_TOL,
    CHALLENGER_STABILITY_TOL,
)

from ._candidates import CANDIDATES
from ._metrics import score


def paired_ci(champ_storm, chall_storm, seed):
    """Mean per-storm Brier difference (champion − challenger; > 0 means the
    challenger is better) with a storm-bootstrap confidence interval."""
    d = np.asarray(champ_storm) - np.asarray(chall_storm)
    rng = np.random.RandomState(seed)
    boots = d[rng.randint(0, len(d), (CHALLENGER_CI_BOOTSTRAPS, len(d)))].mean(1)
    a = (1 - CHALLENGER_CI_LEVEL) / 2
    return {"mean": float(d.mean()),
            "ci_low": float(np.quantile(boots, a)),
            "ci_high": float(np.quantile(boots, 1 - a))}


def _mean(gauges, name, *path):
    vals = []
    for g in gauges:
        v = g["stability"][name]
        for key in path:
            v = v.get(key) if isinstance(v, dict) else None
        if v is not None:
            vals.append(v)
    return float(np.mean(vals)) if vals else None


def pool(gauges, seed):
    """Pooled accuracy, mean stability, per-gauge paired CIs and Wilcoxon tests."""
    champ = CHALLENGER_CHAMPION
    y = np.concatenate([g["_y"] for g in gauges])
    models = {}
    for name, spec in CANDIDATES.items():
        p = np.concatenate([g["_oof"][name] for g in gauges])
        per_gauge = [g["accuracy"][name]["brier"] for g in gauges]
        models[name] = {
            "label": spec["label"],
            "accuracy": score(y, p),
            "brier_gauge_median": float(np.median(per_gauge)),
            "brier_gauge_worst": float(np.max(per_gauge)),
            "seed_grid_sd": _mean(gauges, name, "seed", "grid_sd_mean"),
            "bootstrap_grid_sd": _mean(gauges, name, "bootstrap", "grid_sd_mean"),
            "bootstrap_brier_sd": _mean(gauges, name, "bootstrap", "brier_sd"),
            "monotone_violation_rate": _mean(gauges, name, "shape", "monotone_violation_rate"),
            "roughness": _mean(gauges, name, "shape", "roughness"),
        }
        if name == champ:
            continue
        cis = [paired_ci(g["_storm_brier"][champ], g["_storm_brier"][name], seed)
               for g in gauges]
        for g, ci in zip(gauges, cis):
            g.setdefault("vs_champion", {})[name] = ci
        diffs = [g["accuracy"][champ]["brier"] - g["accuracy"][name]["brier"]
                 for g in gauges]
        test = {"n_gauges": len(gauges), "median_diff": float(np.median(diffs))}
        if len(gauges) >= CHALLENGER_MIN_WILCOXON_GAUGES and any(diffs):
            test["method"] = "wilcoxon"
            test["p_value"] = float(wilcoxon(diffs, alternative="greater").pvalue)
            test["challenger_better"] = test["p_value"] < CHALLENGER_ALPHA
        else:
            test["method"] = "all_gauge_cis"
            test["p_value"] = None
            test["challenger_better"] = all(ci["ci_low"] > 0 for ci in cis)
        models[name]["vs_champion"] = test
    return models


def _le(a, b, tol):
    """``a`` no worse than ``b`` (lower is better), with slack; None counts as 0."""
    return (a or 0.0) <= (b or 0.0) + tol


def decide(models):
    """Apply the decision rule against the best challenger by pooled Brier.

    The GBM is retained if it passes all three tests (accuracy, stability,
    shape), replaced if it fails all three, and escalated otherwise.
    """
    champ = models[CHALLENGER_CHAMPION]
    challengers = {n: m for n, m in models.items() if n != CHALLENGER_CHAMPION}
    best_name = min(challengers, key=lambda n: challengers[n]["accuracy"]["brier"])
    best = challengers[best_name]

    cb, bb = champ["accuracy"]["brier"], best["accuracy"]["brier"]
    accuracy_ok = (cb <= bb * (1 + CHALLENGER_BRIER_TOLERANCE)
                   and not best["vs_champion"]["challenger_better"])
    stability_ok = (_le(champ["seed_grid_sd"], best["seed_grid_sd"], CHALLENGER_STABILITY_TOL)
                    and _le(champ["bootstrap_grid_sd"], best["bootstrap_grid_sd"],
                            CHALLENGER_STABILITY_TOL))
    shape_ok = _le(champ["monotone_violation_rate"], best["monotone_violation_rate"],
                   CHALLENGER_MONOTONE_RATE_TOL)

    tests = {"accuracy": accuracy_ok, "stability": stability_ok, "shape": shape_ok}
    passed = sum(tests.values())
    outcome = "retain" if passed == 3 else "replace" if passed == 0 else "escalate"
    return {
        "champion": CHALLENGER_CHAMPION,
        "best_challenger": best_name,
        "brier_champion": cb,
        "brier_best_challenger": bb,
        "brier_gap_pct": 100.0 * (cb - bb) / bb if bb else None,
        "tests": tests,
        "outcome": outcome,
    }
