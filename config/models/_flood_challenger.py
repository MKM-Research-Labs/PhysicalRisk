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

"""Flood-classifier challenger benchmark parameters (GBM vs Random Forest).

The protocol is set out in the Stress Testing guide, section "Model Selection:
Challenger Comparison" (docs/models/stress_testing/stress_testing_guide.tex).
The tool is tools/flood_classifier_challenger.  Defaults are sized so one gauge
runs in minutes; a full sign-off run raises the seed and bootstrap counts.
"""

CHALLENGER_OUT_DIR = "docs/models/stress_testing/challenger"
CHALLENGER_RESULTS_JSON = "challenger_results.json"
CHALLENGER_RESULTS_TEX = "challenger_results.tex"

# Fits run in parallel across this many processes (-1: every core).
CHALLENGER_N_JOBS = -1

# Data: storms sampled from the catalogue per gauge, and the sampling seed.
CHALLENGER_N_STORMS = 1000
CHALLENGER_SEED = 20261029

# Held-out scoring: storms are split into this many GroupKFold folds.
CHALLENGER_FOLDS = 5

# Tuning: random-search trials per tunable model per fold (the model's
# default configuration is always trial 0), scored on one inner storm split.
CHALLENGER_TUNE_TRIALS = 6
CHALLENGER_INNER_HOLDOUT = 0.25

# Calibrated Random Forest: share of training storms held back for isotonic fit.
CHALLENGER_CALIB_HOLDOUT = 0.25

# Stability tests (doc: 20 seeds, 50 storm bootstraps for sign-off).
CHALLENGER_SEEDS = 10
CHALLENGER_BOOTSTRAPS = 20

# Probability-surface grid: water level spans these quantiles of log(h/s) in
# the real data; time is every CHALLENGER_GRID_HOUR_STEP hours; Δ and Δ² are 0.
CHALLENGER_GRID_LEVEL_QUANTILES = (0.01, 0.995)
CHALLENGER_GRID_LEVEL_POINTS = 41
CHALLENGER_GRID_HOUR_STEP = 6
# A fall in P(flood) larger than this as the level rises is a violation.
CHALLENGER_MONOTONE_TOL = 1e-3

# Metrics and statistics.
CHALLENGER_ECE_BINS = 10
CHALLENGER_PROB_CLIP = 1e-6
CHALLENGER_CI_BOOTSTRAPS = 1000
CHALLENGER_CI_LEVEL = 0.95

# Decision rule: the GBM may be worse on pooled Brier by at most this fraction,
# and a challenger is "significantly better" below this Wilcoxon p-value.
CHALLENGER_BRIER_TOLERANCE = 0.02
CHALLENGER_ALPHA = 0.05
# Stability and shape comparisons allow this much slack before the GBM counts
# as worse: probability s.d. (absolute) and monotonicity violation rate.
CHALLENGER_STABILITY_TOL = 0.002
CHALLENGER_MONOTONE_RATE_TOL = 0.005
# Wilcoxon across gauges needs at least this many gauges; below it, "challenger
# significantly better" means every gauge's storm-bootstrap CI excludes zero.
CHALLENGER_MIN_WILCOXON_GAUGES = 6

# Candidate models.  "gbm_prod" is the production GBM, untuned (its params come
# from models.stress.flood_classifier._trainer.GBM_PARAMS).
CHALLENGER_CHAMPION = "gbm_prod"
CHALLENGER_RF_PARAMS = {
    "n_estimators": 500,
    "max_features": 2,
    "min_samples_leaf": 50,
}
CHALLENGER_LOGIT_PARAMS = {"C": 1.0, "max_iter": 1000}
CHALLENGER_SEARCH_SPACE = {
    "gbm": {
        "n_estimators": [100, 200, 300, 500],
        "max_depth": [2, 3, 4],
        "learning_rate": [0.02, 0.05, 0.1],
        "subsample": [0.6, 0.8, 1.0],
        "min_samples_leaf": [20, 50, 100],
    },
    "rf": {
        "max_features": [1, 2, 3],
        "min_samples_leaf": [10, 20, 50, 100, 200],
        "max_depth": [None, 8, 12, 16],
    },
    "logit": {
        "C": [0.01, 0.1, 1.0, 10.0],
    },
}

# Synthetic catalogue for smoke runs and tests (no storm data needed).
CHALLENGER_SYNTH_BASE_LEVEL = 1.0
CHALLENGER_SYNTH_SEVERE_LEVEL = 3.0
CHALLENGER_SYNTH_PEAK_RANGE = (0.5, 1.3)   # peak as a fraction of severe
CHALLENGER_SYNTH_RISE_HOURS = (10, 80)
CHALLENGER_SYNTH_DECAY = (0.02, 0.08)
CHALLENGER_SYNTH_NOISE = 0.02              # level noise as a fraction of severe
