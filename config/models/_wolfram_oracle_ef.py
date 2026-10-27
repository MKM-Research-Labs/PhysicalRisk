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

"""Wolfram oracle benchmark parameters for MKM-EF-001 (Event Frequency Model).

The cases a benchmark run checks EF-001's frequency maths against, the claims in
its document of record (``docs/storm_freq/event_frequency_plan.pdf`` v2.3) it
tests, and where it files its evidence.
"""

# The code under test: pure-maths files, loaded under stand-in packages rooted here
# (the package __init__ reaches the data store).
ORACLE_EF_ROOT = "src/models/frequency"
ORACLE_EF_SOURCES = {
    "annualise": "src/models/frequency/annualise.py",
    "rate_process": "src/models/frequency/rate_process.py",
    "negbin": "src/models/frequency/families/_negbin.py",
    "poisson": "src/models/frequency/families/_poisson.py",
    "select": "src/models/frequency/families/_select.py",
    "reconcile": "src/models/frequency/ylt/_reconcile.py",
}
# The term structure the per-year hazards feed (GH-001's code).
ORACLE_EF_TERM_SOURCE = "src/models/hazard/gev.py"

ORACLE_EF_OUT_DIR = "docs/models/event_frequency_benchmark"
ORACLE_EF_DOC = "MKM-EF-001_wolfram_benchmark"
ORACLE_EF_CSV = "frequency.csv"
ORACLE_EF_WL = "frequency.wl"
ORACLE_EF_TABLE_PREFIX = "evidence_tables_"

ORACLE_EF_MODEL_ID = "MKM-EF-001"
ORACLE_EF_MODEL_NAME = "Event Frequency Model"

# Annualisation (Eq. 2): arrival rates in events a year, per-event probabilities.
ORACLE_EF_LAMBDAS = (0.5, 2.0, 5.0, 10.0, 20.0, 50.0)
ORACLE_EF_P_EVENTS = (1e-6, 1e-4, 1e-3, 0.01, 0.05, 0.2, 0.5)
ORACLE_EF_TENORS = (1, 3, 5, 10)
# A rising arrival rate for the non-stationary term structure: lambda_y = l0 (1 + g)^y.
ORACLE_EF_TREND = (5.0, 0.05)

# Compound-Poisson year loss (Stage 6): synthetic catalogues, seeded.
ORACLE_EF_SEED = 20261026
ORACLE_EF_CATALOGUES = ((20, 2.0), (50, 5.0), (200, 12.0))   # (events, lambda_effective)
ORACLE_EF_LOSS_YEARS = 10_000

# Family selection: synthetic annual count series, seeded. kind: poisson (mean),
# negbin (mean, alpha), binomial (trials, prob) for under-dispersion.
ORACLE_EF_COUNT_SERIES = (
    ("poisson", 30, (6.0,)), ("poisson", 50, (12.0,)),
    ("negbin", 30, (8.0, 0.3)), ("negbin", 50, (12.0, 0.1)),
    ("negbin", 25, (4.0, 1.0)), ("negbin", 60, (20.0, 0.05)),
    ("binomial", 30, (20, 0.3)),
)

# Model against reference.
ORACLE_EF_REL_TOL = 1e-12          # closed forms
# lambda p below which annualisation is outside the operating range: 1 - exp(-x)
# loses about 1e-16/x relative there, and is reported rather than judged.
ORACLE_EF_OPERATING_MIN_X = 1e-4
ORACLE_EF_PVALUE_TOL = 1e-10       # chi-square p-values (scipy's incomplete gamma)
ORACLE_EF_LL_TOL = 1e-8            # NegBin search: log-likelihood short of the maximum

# The document's claims, tested as stated:
#   s5.9 Eq. 4  E[(1-p)^N] = exp(-lambda p) for N ~ Poisson(lambda), so the closed
#               form is the simulation's exact expectation; the aggregate view is lambda p;
#   s5.9        the gate statistic is a z-score: mean |z| = sqrt(2/pi) = 0.798;
#   s7.2        sampling error ~5%, ~1.6%, ~0.5%, ~0.16% at 1e3..1e6 years;
#   annualise   per-year hazards follow "the annual probability used as the per-year
#               hazard", not the exact 1 - exp(-p sum lambda) -- measured here.
ORACLE_EF_CLAIM_MEAN_ABS_Z = 0.798
ORACLE_EF_CLAIM_SAMPLING = ((1_000, 0.05), (10_000, 0.016), (100_000, 0.005), (1_000_000, 0.0016))
