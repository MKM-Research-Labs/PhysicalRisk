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

"""Wolfram oracle benchmark parameters for MKM-DE-001 (Delta Engine).

The cases a benchmark run checks the delta engine's pricer against, the claims
in DE-001's model document (``delta_engine.pdf`` v1.0) it tests, and where it
files its evidence. Shared settings -- kernel, precision -- are in ``_wolfram_oracle``.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_DE_PACKAGE = "models.trading.delta_engine.pricer"
ORACLE_DE_SOURCES = ("src/models/trading/delta_engine/pricer.py",
                     "src/models/trading/delta_engine/engine.py")

ORACLE_DE_OUT_DIR = "docs/models/delta_engine_benchmark"
ORACLE_DE_DOC = "MKM-DE-001_wolfram_benchmark"
ORACLE_DE_CSV = "delta.csv"
ORACLE_DE_WL = "delta.wl"
ORACLE_DE_TABLE_PREFIX = "evidence_tables_"

ORACLE_DE_MODEL_ID = "MKM-DE-001"
ORACLE_DE_MODEL_NAME = "Delta Engine"

# The case grid: annual hazard rates from below the 2 bp spread floor to 0.5,
# the book's tenors plus a 10-year stress, recovery 0 as booked, and both curves.
ORACLE_DE_RATES = (0.0001, 0.0005, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
ORACLE_DE_TENORS = (1, 2, 3, 4, 5, 10)
ORACLE_DE_NOTIONAL = 10_000_000          # a book notional (config.port NOTIONALS)
ORACLE_DE_TRADE_SPREAD_BPS = 150.0       # an inception spread for the MTM check

# Model against reference. The engine rounds what it returns -- the spread change
# to 1e-4 bp, FS01 and MTM to the penny, the annuity to 1e-6 -- so those outputs
# are judged to half a unit in their last place; the unrounded annuity to:
ORACLE_DE_ANNUITY_TOL = 1e-12
ORACLE_DE_ROUNDING = {"delta_spread_bps": 1e-4, "dv01_gbp": 1e-2, "risky_annuity": 1e-6,
                      "mtm": 1e-2}

# The model document's claims, tested as stated:
#   s6.5  the 1 bp bump's finite-difference error is below this, in bp, against
#         the analytical gradient;
#   s6.1  FS01 "scales approximately linearly with hazard rate" over 50-500 bp --
#         read as FS01(500 bp)/FS01(50 bp) within this fraction of 10;
#   s6.2  a 5Y trade has "approximately 4.5x" the FS01 of a 1Y -- within this;
#   s6.3  a 100 bp parallel yield shift changes FS01 by "approximately 3-5%";
#   s7.2  the hand-calculated risky annuity, 3Y at 200 bp and 4% flat, "~2.738";
#   s8.1  FS01 x dh against full revaluation for a 50 bp move.
ORACLE_DE_CLAIM_FD_BP = 0.01
ORACLE_DE_CLAIM_LINEAR = (0.005, 0.05)
ORACLE_DE_CLAIM_LINEAR_TOL = 0.25
ORACLE_DE_CLAIM_TENOR = (1, 5, 4.5, 0.25)          # short, long, ratio, tolerance
ORACLE_DE_CLAIM_YIELD_SHIFT = 0.01
ORACLE_DE_CLAIM_YIELD_RANGE = (0.03, 0.05)
ORACLE_DE_CLAIM_HAND = (0.02, 3, 0.04, 2.738)       # rate, tenor, flat r, stated A
ORACLE_DE_CLAIM_HAND_DP = 3                         # the document quotes 3 dp
ORACLE_DE_CLAIM_MOVE = 0.005
ORACLE_DE_FLAT_RATE = 0.03                          # the engine's default flat rate
# Step for the reference's high-precision central difference of s(h). It must
# survive the 50-digit evaluation of s; mpmath's default step does not, and
# returns a zero gradient where h is a short binary fraction such as 0.5.
ORACLE_DE_GRADIENT_STEP = 1e-20
ORACLE_DE_TABLE_TENOR = 5
