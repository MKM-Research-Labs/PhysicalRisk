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

"""Run the benchmark over a set of gauges and write the results."""

import datetime as _dt
import time
from pathlib import Path

from config.models import (
    CHALLENGER_BOOTSTRAPS,
    CHALLENGER_FOLDS,
    CHALLENGER_N_JOBS,
    CHALLENGER_N_STORMS,
    CHALLENGER_OUT_DIR,
    CHALLENGER_RESULTS_JSON,
    CHALLENGER_RESULTS_TEX,
    CHALLENGER_SEED,
    CHALLENGER_SEEDS,
    CHALLENGER_TUNE_TRIALS,
)

from ._benchmark import evaluate_gauge
from ._data import load_catalogue, synthetic_catalogue
from ._decision import decide, pool
from ._report import write_json, write_tex


def run_benchmark(gauges="all", max_gauges=None, synthetic=0,
                  n_storms=CHALLENGER_N_STORMS, folds=CHALLENGER_FOLDS,
                  tune_trials=CHALLENGER_TUNE_TRIALS, seeds=CHALLENGER_SEEDS,
                  bootstraps=CHALLENGER_BOOTSTRAPS, seed=CHALLENGER_SEED,
                  out_dir=CHALLENGER_OUT_DIR, n_jobs=CHALLENGER_N_JOBS, log=print) -> dict:
    """Score every candidate on each gauge, pool, decide, and write reports.

    ``synthetic=n`` runs on n synthetic gauges instead of the storm catalogue.
    ``n_jobs`` processes run the fits (1 runs them in this process).
    Returns the results dict (with private per-row arrays).
    """
    t0 = time.time()
    if synthetic:
        sets, source = synthetic_catalogue(synthetic, n_storms, seed), "synthetic"
    else:
        sets, source = load_catalogue(gauges, n_storms, seed, max_gauges), "catalogue"

    results = []
    for gs in sets:
        log(f"  {gs.gauge_id}: {len(set(gs.groups[:gs.n_real])):,} storms, "
            f"{gs.n_real:,} rows, flood rate {gs.y[:gs.n_real].mean():.1%}")
        results.append(evaluate_gauge(gs, folds, tune_trials, seeds, bootstraps, seed, log, n_jobs))

    scored = [g for g in results if g["status"] == "scored"]
    if not scored:
        raise RuntimeError("no gauge could be scored")
    models = pool(scored, seed)
    out = {
        "meta": {
            "date": _dt.date.today().isoformat(),
            "source": source,
            "n_gauges_scored": len(scored),
            "n_gauges_skipped": len(results) - len(scored),
            "n_storms": n_storms, "folds": folds, "tune_trials": tune_trials,
            "seeds": seeds, "bootstraps": bootstraps, "seed": seed, "n_jobs": n_jobs,
            "seconds": round(time.time() - t0, 1),
        },
        "models": models,
        "decision": decide(models),
        "gauges": results,
    }
    if out_dir:
        out_dir = Path(out_dir)
        write_json(out, out_dir / CHALLENGER_RESULTS_JSON)
        write_tex(out, out_dir / CHALLENGER_RESULTS_TEX)
        log(f"  wrote {out_dir / CHALLENGER_RESULTS_JSON} and {CHALLENGER_RESULTS_TEX}")
    return out
