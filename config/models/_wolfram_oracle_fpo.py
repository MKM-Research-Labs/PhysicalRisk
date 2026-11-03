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
"""Wolfram oracle benchmark parameters for MKM-FPO-001 (Flood Polynomial Model).

The cases a benchmark run evaluates, the model document it tests (``flood_poly.pdf``
v1.0, 28-Mar-2026), the GBM classifiers it is judged against, and where it files
its evidence.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_FPO_MODULES = {"poly": "models.stress.flood_poly", "sensitivity": "models.stress.sensitivity"}
ORACLE_FPO_SOURCES = ("src/models/stress/flood_poly.py", "src/models/stress/sensitivity.py",
                      "config/models/_misc.py")
ORACLE_FPO_JS = "src/static/js/trading/port_stress/setup.js"

ORACLE_FPO_OUT_DIR = "docs/models/flood_poly_benchmark"
ORACLE_FPO_DOC = "MKM-FPO-001_wolfram_benchmark"
ORACLE_FPO_CSV = "floodpoly.csv"
ORACLE_FPO_WL = "floodpoly.wl"
ORACLE_FPO_TABLE_PREFIX = "evidence_tables_"

# The document's model (v1.0, s3-s4): P = sigma(sum_k c_k h^i t^j), h = ln max(w/s, eps),
# t = ln((hour + 1)/T), the exponent clamped. Terms as (i, j), coefficients as printed.
ORACLE_FPO_DOC_VERSION = "v1.0"
ORACLE_FPO_DOC_TERMS = ((1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (0, 0))
ORACLE_FPO_DOC_COEFFS = ("28.9582", "-11.6351", "26.5490", "-22.8893", "-7.0794", "-0.8872")
ORACLE_FPO_DOC_HOURS = 168
ORACLE_FPO_DOC_EPS = "1e-8"
ORACLE_FPO_DOC_CLAMP = 30

ORACLE_FPO_CODE_TOL = 1e-12
ORACLE_FPO_WOLFRAM_TOL = 1e-25

# The cases: severe thresholds, w/s ratios and hours spanning the document's range.
ORACLE_FPO_SEVERE = (6.58, 3.0, 12.4)
ORACLE_FPO_RATIOS = (0.0, 1e-9, 0.3, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0, 1.05, 1.2, 1.5)
ORACLE_FPO_HOURS = (0, 1, 6, 12, 24, 36, 48, 72, 96, 120, 144, 160, 167)
# Where Wolfram solves P = 1/2 for the level, and evaluates dP/dh.
ORACLE_FPO_CONTOUR_HOURS = (24, 48, 72, 96, 120, 167)

# The GBM classifiers (MKM-FC-001) the polynomial approximates, on the real storm
# states production trains them on (the challenger's catalogue loader): storms drawn
# once with this seed, every gauge with a classifier. Near severe is w/s >= 0.75.
ORACLE_FPO_GAUGE = "GAUGE-dc5e88fb"           # the gauge the document fitted to
ORACLE_FPO_STORMS = 2000
ORACLE_FPO_SEED = 7
ORACLE_FPO_NEAR = 0.75
ORACLE_FPO_CLAIM_DELTA = 0.05                 # s8: |poly - GBM| below 0.05 across the surface
