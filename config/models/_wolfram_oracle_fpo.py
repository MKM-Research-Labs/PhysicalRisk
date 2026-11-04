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

The cases a benchmark run evaluates, the model document it tests (``flood_poly_v2.0.pdf``,
03-Nov-2026), the GBM classifiers it is judged against, and where it files its evidence.
v0.1 tested v1.0 (commit fcd060afa); this tests v2.0.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_FPO_MODULES = {"poly": "models.stress.flood_poly", "sensitivity": "models.stress.sensitivity",
                      "fit": "tools.flood_poly_fit.fit"}
ORACLE_FPO_SOURCES = ("src/models/stress/flood_poly.py", "src/models/stress/sensitivity.py",
                      "config/models/_misc.py", "src/routes/trading/stress/flood_poly.py",
                      "tools/flood_poly_fit/fit.py")
ORACLE_FPO_JS = "src/static/js/trading/port_stress/setup.js"
ORACLE_FPO_SCENARIO = "src/routes/trading/stress/scenario.py"
ORACLE_FPO_NODE = "node"                      # the JavaScript is run here, if it is installed

ORACLE_FPO_OUT_DIR = "docs/models/flood_poly_benchmark"
ORACLE_FPO_DOC = "MKM-FPO-001_wolfram_benchmark"
ORACLE_FPO_CSV = "floodpoly.csv"
ORACLE_FPO_WL = "floodpoly.wl"
ORACLE_FPO_TABLE_PREFIX = "evidence_tables_"

# The document's model (v2.0, s3): P = 1 at or above severe; below it
# P = sigma(sum_k c_k h^i t^j) at h = ln max(w/s, floor) and t held at the support
# envelope, interpolated linearly in t between its knots; the exponent clamped.
ORACLE_FPO_DOC_VERSION = "v2.0"
ORACLE_FPO_DOC_TERMS = ((1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (3, 0), (0, 3), (2, 1), (1, 2), (0, 0))
ORACLE_FPO_DOC_HOURS = 168
ORACLE_FPO_DOC_FLOOR = "0.2"
ORACLE_FPO_DOC_CLAMP = 30
ORACLE_FPO_DOC_SLOPE_MARGIN = 0.01           # s3.4: the fit holds dz/dh at least this

ORACLE_FPO_CODE_TOL = 1e-12
ORACLE_FPO_WOLFRAM_TOL = 1e-25

# The cases: severe thresholds, w/s ratios (through the floor, the envelope's knots and
# beyond severe) and hours (through the envelope).
ORACLE_FPO_SEVERE = (6.58, 3.0, 12.4)
ORACLE_FPO_RATIOS = (0.0, 1e-9, 0.1, 0.2, 0.3, 0.326, 0.33, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9,
                     0.95, 0.99, 1.0, 1.05, 1.2, 1.5)
ORACLE_FPO_HOURS = (0, 1, 2, 3, 5, 8, 12, 16, 24, 30, 36, 38, 48, 72, 96, 120, 144, 160, 167)
# Where Wolfram differentiates P in the level at a fixed hour: held and not.
ORACLE_FPO_SLOPE_POINTS = ((0.52, 0), (0.83, 0), (0.52, 24), (0.83, 48), (0.97, 96), (0.6, 167))
ORACLE_FPO_FINE_LEVELS = 2000                # the code's surface is checked monotone on this many
ORACLE_FPO_LATE_HOUR = 16                    # s3.2: from this hour on, P never rises with the hour
ORACLE_FPO_EARLY_RISE = 0.06                 # s3.2: before it, by at most this

# The GBM classifiers (MKM-FC-001) the polynomial approximates, on the real storm
# states production trains them on (the challenger's catalogue loader): storms drawn
# once with this seed, every gauge with a classifier. Near severe is w/s >= 0.75.
ORACLE_FPO_STORMS = 2000
ORACLE_FPO_SEED = 7
ORACLE_FPO_NEAR = 0.75
ORACLE_FPO_ENVELOPE_TOL = 0.1                # hours: the printed envelope, recomputed
