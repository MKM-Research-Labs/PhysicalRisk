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

"""Wolfram oracle benchmark parameters — tools/wolfram_oracle (MKM-GH-001).

The cases a benchmark run checks GH-001's GEVFitter against, and where the run
files its evidence. Changing a case changes the evidence, so they live here
rather than in the tool.
"""

# Where a run writes its report, CSVs and Wolfram scripts, under the project root.
ORACLE_GEV_OUT_DIR = "docs/models/benchmark/gev_hazard"
ORACLE_GEV_REPORT_PDF = "gev_hazard_benchmark.pdf"
ORACLE_GEV_RETURN_LEVELS_CSV = "return_levels.csv"
ORACLE_GEV_FIT_CSV = "fit.csv"
ORACLE_GEV_RETURN_LEVELS_WL = "return_levels.wl"
ORACLE_GEV_FIT_WL = "fit.wl"
# Each .wl writes its results beside itself under this suffix.
ORACLE_WOLFRAM_SUFFIX = "_wolfram.json"

ORACLE_MODEL_ID = "MKM-GH-001"
ORACLE_MODEL_NAME = "GEV Hazard Curve Model"

ORACLE_REFERENCE_DPS = 50  # mpmath working digits for the closed-form reference
ORACLE_WOLFRAM_DIGITS = 30  # N[expr, d] — real digits, because inputs go over exact

# name: (mu, sigma, xi). xi > 0 is a heavy Frechet tail (EVT convention).
ORACLE_GEV_CASES = {
    "gumbel": (100.0, 20.0, 0.0),
    "frechet_moderate": (100.0, 20.0, 0.2),
    "frechet_heavy": (100.0, 20.0, 0.5),
    "weibull_bounded": (100.0, 20.0, -0.2),
    "near_zero_shape": (100.0, 20.0, 1e-9),
    "below_gumbel_switch": (100.0, 20.0, 1e-11),  # GEVFitter rounds this to Gumbel
}
ORACLE_RETURN_PERIODS = (10, 100, 200, 1000, 10000, 1_000_000)
# Return periods the model is used at; errors beyond are reported, not judged.
ORACLE_OPERATING_MAX_T = 10000
# A model value further than this from the reference is a benchmark failure.
ORACLE_REL_TOL = 1e-9

ORACLE_FIT_SEED = 20261019
# name: (n, mu, sigma, xi) — the truth each synthetic sample is drawn from
ORACLE_FIT_SYNTHETIC = {
    "n30_xi0.1": (30, 3.0, 0.4, 0.1),
    "n50_xi0.3": (50, 3.0, 0.4, 0.3),
    "n200_xi-0.1": (200, 3.0, 0.4, -0.1),
    "n30_xi0.4": (30, 3.0, 0.4, 0.4),
}
ORACLE_FIT_ROUND_DP = 4  # peak levels are persisted to 4 dp (hazard io _save)
ORACLE_FIT_CHECK_T = (100, 1000)
ORACLE_FIT_XI_STARTS = (-0.3, -0.1, 0.0, 0.1, 0.3, 0.5)
ORACLE_FIT_OPT_TOL = 1e-12
ORACLE_FIT_MAX_ITER = 20000
# A log-likelihood gain below this is optimiser tolerance, not a missed maximum.
ORACLE_FIT_LL_TOL = 1e-4
