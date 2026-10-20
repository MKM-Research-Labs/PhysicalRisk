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

"""Wolfram oracle benchmark parameters for MKM-SI-001 (Storm Intensity Distribution).

The cases a benchmark run checks ``IntensityDistribution`` against, the claims in
SI-001's model document (``storm_intensity.pdf``, v1.3) it tests, and where it
files its evidence. Shared settings -- kernel, precision -- are in ``_wolfram_oracle``.
"""

# The code under test: imported as a package (its __init__ touches no data store),
# with these two files named in the evidence.
ORACLE_SI_PACKAGE = "models.intensity"  # as production imports it (config puts src/ on the path)
ORACLE_SI_SOURCES = ("src/models/intensity/distribution/_core.py",
                     "src/models/intensity/distribution/_math.py")

ORACLE_SI_OUT_DIR = "docs/models/storm_intensity_benchmark"
ORACLE_SI_DOC = "MKM-SI-001_wolfram_benchmark"
ORACLE_SI_CSV = "intensity.csv"
ORACLE_SI_WL = "intensity.wl"
ORACLE_SI_TABLE_PREFIX = "evidence_tables_"

ORACLE_SI_MODEL_ID = "MKM-SI-001"
ORACLE_SI_MODEL_NAME = "Storm Intensity Distribution"

# The case grid, over every scenario family the model ships.
ORACLE_SI_X_STEP = 2.5                     # exceedance checked at every 2.5 from Imin to Imax
ORACLE_SI_P_EXPONENTS = range(1, 7)        # quantile at p = 10^-k ...
ORACLE_SI_P_MULTIPLIERS = (1, 2, 5)        # ... x 1, 2, 5, plus 1 - those
ORACLE_SI_RETURN_PERIODS = (2, 5, 10, 25, 50, 100, 200, 500, 1000)
ORACLE_SI_STORMS_PER_YEAR = 20             # the document's default (s3.6)
# Acklam's inverse normal is checked on its own over a finer grid, both tails.
ORACLE_SI_ACKLAM_EXPONENTS = range(1, 16)
ORACLE_SI_ACKLAM_BODY_STEP = 0.01

# Model against reference: the exceedance is closed form (erf), the quantile
# carries Acklam's error through mu + sigma * z.
ORACLE_SI_EXC_TOL = 1e-12
ORACLE_SI_INV_TOL = 1e-8

# The model document's claims, tested as stated:
#   s3.5, s5.3  Acklam's approximation "accurate to approximately 1.15e-9 in absolute
#         error across the full domain";
#   s8.4  clamping "creates a slight probability mass distortion" -- read here as
#         at most this fraction of storms at either bound;
#   s5.4, s8.5  jitter "does not materially affect the distributional moments" -- read
#         as a relative change in the mean and standard deviation below this.
ORACLE_SI_CLAIM_ACKLAM = 1.15e-9
ORACLE_SI_CLAIM_SLIGHT_MASS = 0.01
ORACLE_SI_CLAIM_JITTER_REL = 0.01
ORACLE_SI_JITTER_SD = 0.5                  # the jitter the model adds (s3.7)
