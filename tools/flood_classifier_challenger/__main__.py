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

"""CLI: python -m tools.flood_classifier_challenger [--gauges all|G1,G2] ..."""

import argparse
from pathlib import Path

from tools.flood_classifier_challenger import run_benchmark

from config.models import (
    CHALLENGER_BOOTSTRAPS,
    CHALLENGER_FOLDS,
    CHALLENGER_N_JOBS,
    CHALLENGER_N_STORMS,
    CHALLENGER_OUT_DIR,
    CHALLENGER_SEED,
    CHALLENGER_SEEDS,
    CHALLENGER_TUNE_TRIALS,
)

_ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gauges", default="all",
                    help="'all' or comma-separated gauge ids")
    ap.add_argument("--max-gauges", type=int, default=None)
    ap.add_argument("--synthetic", type=int, default=0, metavar="N",
                    help="run on N synthetic gauges (no storm data needed)")
    ap.add_argument("--n-storms", type=int, default=CHALLENGER_N_STORMS)
    ap.add_argument("--folds", type=int, default=CHALLENGER_FOLDS)
    ap.add_argument("--tune-trials", type=int, default=CHALLENGER_TUNE_TRIALS)
    ap.add_argument("--seeds", type=int, default=CHALLENGER_SEEDS)
    ap.add_argument("--bootstraps", type=int, default=CHALLENGER_BOOTSTRAPS)
    ap.add_argument("--seed", type=int, default=CHALLENGER_SEED)
    ap.add_argument("--jobs", type=int, default=CHALLENGER_N_JOBS,
                    help="parallel fit processes (-1: every core)")
    ap.add_argument("--out", default=str(_ROOT / CHALLENGER_OUT_DIR))
    a = ap.parse_args(argv)

    gauges = "all" if a.gauges == "all" else [g.strip() for g in a.gauges.split(",")]
    out = run_benchmark(gauges=gauges, max_gauges=a.max_gauges, synthetic=a.synthetic,
                        n_storms=a.n_storms, folds=a.folds, tune_trials=a.tune_trials,
                        seeds=a.seeds, bootstraps=a.bootstraps, seed=a.seed,
                        out_dir=a.out, n_jobs=a.jobs)
    d = out["decision"]
    print(f"\n  Best challenger: {d['best_challenger']}  "
          f"(Brier GBM {d['brier_champion']:.4f} vs {d['brier_best_challenger']:.4f})")
    print(f"  Tests: {d['tests']}  ->  {d['outcome'].upper()}")


if __name__ == "__main__":
    main()
