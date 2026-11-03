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

"""Wolfram oracle benchmark parameters for MKM-GHD-001 (Gauge Historical Daily).

The gauges a benchmark run generates, the claims in GHD-001's model document
(``gaugehd_synthetic.pdf`` v1.0) it tests, and where it files its evidence.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_GHD_MODULE = "models.statistics.synthetic"
ORACLE_GHD_SOURCES = ("src/models/statistics/synthetic.py", "src/port/src/gauge/gaugehd/synthetic.py")

ORACLE_GHD_OUT_DIR = "docs/models/gauge_historical_benchmark"
ORACLE_GHD_DOC = "MKM-GHD-001_wolfram_benchmark"
ORACLE_GHD_CSV = "gaugehd.csv"
ORACLE_GHD_WL = "gaugehd.wl"
ORACLE_GHD_TABLE_PREFIX = "evidence_tables_"

ORACLE_GHD_MODEL_ID = "MKM-GHD-001"
ORACLE_GHD_MODEL_NAME = "Gauge Historical Daily"

# The gauges: each tidal regime with no recorded severe exceedance (the model's
# floor of one) and with eight, on the default thresholds, no historical-high date.
ORACLE_GHD_THRESHOLDS = {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0}
ORACLE_GHD_HISTORICAL_HIGH = 5.5
ORACLE_GHD_REGIMES = ("Non-tidal", "Partially tidal", "Tidal")
ORACLE_GHD_N3 = (0, 8)
ORACLE_GHD_YEARS = 50

# Each gauge is generated this many times, seeds 1..n, and each statistic's mean
# over them is judged against its exact expectation in standard errors.
ORACLE_GHD_REPLICATIONS = 200
ORACLE_GHD_Z_LIMIT = 4.0
# Gauss-Legendre nodes for the base level mu0 = FloodAlert * U(0.3, 0.5), and the
# age (days since a flood) beyond which the AR(1) memory of the flood is dropped.
ORACLE_GHD_MU_NODES = 24
ORACLE_GHD_MAX_AGE = 400
# The reference is evaluated in double precision; Wolfram at 30 digits.
ORACLE_GHD_WOLFRAM_TOL = 1e-9

# The document's claims, tested as stated:
#   s7.1(1)   lag-1 autocorrelation of a non-tidal series about 0.85;
#   s7.1(3)   days above FloodAlert about 5 max(n3,1) + max(n3,1) over the run;
#   s8.4      the AR(1) produces single-day flood spikes;
#   s5.6      January and July means about +/- A_s about the annual mean;
#   s4.5      each history reproduces the observed severe-event frequency, with
#             FrequencyExceedLevel3 the count over the past 5 years (CDM schema);
#   s6.1      lag-7 autocorrelations 0.32 (phi = 0.85) and 0.028 (phi = 0.6).
ORACLE_GHD_CLAIM_LAG1 = 0.85
ORACLE_GHD_CLAIM_ALERT_PER_EVENT = 1.0
ORACLE_GHD_CLAIM_SEASONAL_TOL = 0.05
ORACLE_GHD_N3_WINDOW_YEARS = 5
ORACLE_GHD_CLAIM_LAG7 = ((0.85, 0.32), (0.6, 0.028))

# The document's Table 1, by regime: (sigma_w, A_s, A_tau) as fractions of mu0, and phi;
# the base-level band and the global parameters of s3 and Table 3.
ORACLE_GHD_TABLE1 = {"Non-tidal": (0.08, 0.30, 0.00, 0.85),
                     "Partially tidal": (0.12, 0.22, 0.06, 0.75),
                     "Tidal": (0.20, 0.20, 0.15, 0.60)}
ORACLE_GHD_BASE_BAND = (0.3, 0.5)
ORACLE_GHD_PHASE_DAYS = 15
ORACLE_GHD_SPRING_NEAP = 14.8
ORACLE_GHD_MINOR_RATIO = 5
ORACLE_GHD_SEVERE_TOP = 0.95                  # severe level ~ U(severe, 0.95 h_max)
ORACLE_GHD_ROUND_HALF = 0.0005                # levels are reported to the millimetre
