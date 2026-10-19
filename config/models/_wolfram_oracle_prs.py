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

"""Wolfram oracle benchmark parameters for MKM-PR-001 (PRS Analytical Pricing).

The cases a benchmark run checks ``compute_prs_spread`` against, the claims in
PR-001's model document (``prs_pricing.pdf``) it tests, and where it files its
evidence. Shared settings — kernel, precision — are in ``_wolfram_oracle``.
"""

# The code under test, relative to the project root.
ORACLE_PRS_SOURCE = "src/models/hazard/prs_analytical.py"

# Where a run writes its evidence; one level below docs/models, as for GH-001.
ORACLE_PRS_OUT_DIR = "docs/models/prs_pricing_benchmark"
ORACLE_PRS_DOC = "MKM-PR-001_wolfram_benchmark"
ORACLE_PRS_SPREADS_CSV = "spreads.csv"
ORACLE_PRS_SPREADS_WL = "spreads.wl"
# Generated LaTeX the document inputs: <prefix>macros.tex, <prefix>claims.tex, ...
ORACLE_PRS_TABLE_PREFIX = "evidence_tables_"

ORACLE_PRS_MODEL_ID = "MKM-PR-001"
ORACLE_PRS_MODEL_NAME = "PRS Analytical Pricing Model"

# The case grid. Annual trigger probabilities run from below the 2 bp floor to the
# 0.999 cap; tenors cover the book's 1-5 years and a 10-year stress.
ORACLE_PRS_PROBS = (0.0001, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 0.999)
ORACLE_PRS_TENORS = (1, 3, 5, 10)
ORACLE_PRS_RECOVERIES = (0.0, 0.4)
# The model document's default flat rate (Eq. 3); the book curve is the production
# DEFAULT_YIELD_CURVE, imported where it is used so the benchmark tracks it.
ORACLE_PRS_FLAT_RATE = 0.03

# A model spread further than this from the reference is a benchmark failure.
ORACLE_PRS_REL_TOL = 1e-9
# The yield-curve interpolation is checked on this grid of times (years).
ORACLE_PRS_INTERP_STEP = 0.125
ORACLE_PRS_INTERP_MAX_T = 10
# Model and reference interpolate the same doubles; they agree to rounding.
ORACLE_PRS_INTERP_TOL = 1e-15

# The model document's claims, tested as stated:
#   s8.3  quarterly vs continuous time: "accurate" for low rates, "up to 2-3 bp"
#         when the annual rate exceeds 0.20;
#   s8.4  flat vs term-structure discounting: "< 1 bp" for a 5-year PRS.
ORACLE_PRS_CLAIM_DISC_SPLIT = 0.20
ORACLE_PRS_CLAIM_DISC_BP = 3.0
ORACLE_PRS_CLAIM_CURVE_TENOR = 5
ORACLE_PRS_CLAIM_CURVE_BP = 1.0
# Probabilities the claims are judged over: the operating range, below the cap.
ORACLE_PRS_CLAIM_MAX_P = 0.5

# The model document's own constants, restated so the reference implements the
# document rather than reading the code under test.
ORACLE_PRS_PERIODS_PER_YEAR = 4      # s3.1.3: quarterly, dt = 0.25
ORACLE_PRS_PROB_CAP = 0.999          # s3.1.1: annual probability capped before Eq. 1
ORACLE_PRS_BPS = 10_000              # Eq. 7
# Tenor of the worked tables in the document (claims and basis), as booked.
ORACLE_PRS_TABLE_TENOR = 5
