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
"""Wolfram oracle benchmark parameters for MKM-DD-001 (Depth-Damage Curve Model).

The cases a benchmark run evaluates, the claims in DD-001's filed model document
(``flood_risk.pdf`` v1.1, 18-Feb-2026) it tests, and where it files its evidence.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_DD_MODULES = {"damage": "models.floodrisk.depth_damage", "velocity": "models.floodrisk.velocity",
                     "spatial": "models.floodrisk.spatial", "risk": "models.floodrisk.risk_analytics"}
ORACLE_DD_SOURCES = ("src/models/floodrisk/depth_damage.py", "src/models/floodrisk/velocity.py",
                     "src/models/floodrisk/spatial.py", "src/models/floodrisk/risk_analytics.py")

ORACLE_DD_OUT_DIR = "docs/models/depth_damage_benchmark"
ORACLE_DD_DOC = "MKM-DD-001_wolfram_benchmark"
ORACLE_DD_CSV = "depthdamage.csv"
ORACLE_DD_WL = "depthdamage.wl"
ORACLE_DD_TABLE_PREFIX = "evidence_tables_"

# The code against the document's formulae, in double precision, and Wolfram against
# the 50-digit reference; the Monte Carlo mean against its exact value, in standard errors.
ORACLE_DD_CODE_TOL = 1e-12
ORACLE_DD_WOLFRAM_TOL = 1e-25
ORACLE_DD_Z_LIMIT = 4.0

# The document's Table 2 and s3.
ORACLE_DD_DOC_ATTENUATION_M = 2000.0
ORACLE_DD_SHOCK = 0.2
ORACLE_DD_MC_DRAWS = 1000
ORACLE_DD_EARTH_R_M = 6371000
ORACLE_DD_DEG_KM = 111.0

# The cases. Table 6's roughness grid and depths at S = 0.005; Table 7's distances and
# lengths; Table 9's depth and slope; the depths of Table 5.
ORACLE_DD_TABLE5_DEPTHS = (0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0)
ORACLE_DD_TABLE6 = {"slope": 0.005, "n": (0.02, 0.03, 0.04, 0.05, 0.06, 0.08), "depths": (0.5, 1.0, 2.0)}
ORACLE_DD_TABLE7 = {"distances": (0, 500, 1000, 2000, 5000, 10000), "lengths": (1000, 2000, 3000, 5000)}
ORACLE_DD_TABLE9 = {"depth": 1.0, "slope": 0.003, "n": (0.025, 0.04, 0.06, 0.1)}
ORACLE_DD_TABLE10 = {"distance": 2000, "lengths": (1000, 2000, 5000)}
ORACLE_DD_SLOPES = (0.005, 0.003, 0.0004, -0.004)

# A synthetic portfolio for the Monte Carlo (s3.4): N properties on a grid near the
# Thames reference point, with values and depths chosen to span every damage band.
ORACLE_DD_PORTFOLIO_N = 40
ORACLE_DD_PORTFOLIO_ORIGIN = (51.5, -0.1)
ORACLE_DD_PORTFOLIO_STEP_DEG = 0.01
ORACLE_DD_CORR = {"distance_m": 2000.0, "base": 0.6}
ORACLE_DD_CURVE_SHIFT = 0.10                   # s6.1: a +/-10% shift of the curve
ORACLE_DD_LATITUDE = 51.5                      # s8(8): the Thames latitude
