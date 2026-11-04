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
"""Wolfram oracle benchmark parameters for MKM-SG-001 (Storm-Gauge Forward Model).

The cases a benchmark run evaluates, the claims in SG-001's model document
(``storm_gauge_v2.0.pdf``, 04-Nov-2026) it tests, and where it files its evidence. The
document's printed tables are in ``_wolfram_oracle_sg_tables``.
"""

# The code under test, imported as the package's own tests import it.
ORACLE_SG_MODULES = {"model": "models.stormgauge.forward_model",
                     "data": "models.stormgauge.data_structures",
                     "factory": "models.stormgauge.storm_factory"}
ORACLE_SG_SOURCES = ("src/models/stormgauge/forward_model/_intensity.py",
                     "src/models/stormgauge/forward_model/_response.py",
                     "src/models/stormgauge/forward_model/_core.py",
                     "src/models/stormgauge/storm_factory.py")
ORACLE_SG_PACKAGE = "src/models/stormgauge"

ORACLE_SG_OUT_DIR = "docs/models/storm_gauge_benchmark"
ORACLE_SG_DOC = "MKM-SG-001_wolfram_benchmark"
ORACLE_SG_CSV = "stormgauge.csv"
ORACLE_SG_WL = "stormgauge.wl"
ORACLE_SG_TABLE_PREFIX = "evidence_tables_"

# The code against the document's equations in double precision, the haversine in
# metres, and Wolfram against the 50-digit reference.
ORACLE_SG_CODE_TOL = 1e-12
ORACLE_SG_METRE_TOL = 1e-6
ORACLE_SG_WOLFRAM_TOL = 1e-25

# The document's constants: Eqs. 1-2's radius, Eq. 13's exponent, Table 3's defaults
# (the step, the lag, the rise and fall constants, and the recession run in fall
# constants) and Table 2's default stages (multiples of the alert).
ORACLE_SG_EARTH_R_KM = 6371
ORACLE_SG_GAMMA = "0.8"
ORACLE_SG_DT, ORACLE_SG_LAG, ORACLE_SG_RISE, ORACLE_SG_DECAY = 0.5, 2.0, 1.0, 12.0
ORACLE_SG_RECESSION = 5
ORACLE_SG_STAGES = {"base": 0.35, "warning": 1.33, "severe": 1.58, "high_of_severe": 1.1}
ORACLE_SG_ALERT = 4.0

# The cases. A default storm (Table 1: 24 h, 25 track points, footprint 40 km,
# triangular, Gaussian 0.5) crossing the Thames west to east; gauges on its track and
# north of it; the other kernels and profiles; and settings (dt, lag, rise, decay) that
# exercise the floor in Eq. 15, a step longer than the rise, and a duration that is not
# a whole number of steps.
ORACLE_SG_TRACK = ((-1.0, 51.5), (0.5, 51.5))
ORACLE_SG_GAUGE = (-0.25, 51.5)
ORACLE_SG_OFFSETS_DEG = (0.0, 0.1, 0.2, 0.4)
ORACLE_SG_PEAKS = (30.0, 50.0, 80.0, 100.0)
ORACLE_SG_SETTINGS = ((0.5, 2.0, 1.0, 12.0), (0.25, 2.0, 1.0, 12.0), (1.0, 3.3, 0.5, 6.0), (0.5, 2.0, 4.0, 24.0))
ORACLE_SG_DURATIONS = (24.0, 23.7, 48.0)

# Claims, as v2.0 states them. s6.2: a +-25% change in gamma moves the target at I=50 by
# +14.9% and -12.9%, and by 10-20% over I=40-60; s3.5: the intensities at which the
# target (steady) and a default storm crossing the gauge reach each stage; s3.6 and
# Table 8: peak level follows peak intensity by 2.5 h; s8(5): the sphere's error against
# WGS84 in the UK, east-west and north-south (%); Q3: timings, judged to within a factor.
ORACLE_SG_GAMMA_STATED = {"at50": (14.9, -12.9), "range": (10, 20)}
ORACLE_SG_STEADY_STATED = {"alert": 38.7, "warning": 64.7, "severe": 86.0, "high": 100.0}
ORACLE_SG_STORM_STATED = {"alert": 40.9, "warning": 68.2, "severe": 90.7}
ORACLE_SG_LAG_STATED_H = 2.5
ORACLE_SG_ELLIPSOID_STATED = {"east_west": 0.32, "north_south": 0.06}
ORACLE_SG_UK_PAIRS = ((51.5, -1.0, 51.5, 0.5), (51.0, -0.3, 52.8, -0.3), (51.2, -1.4, 52.1, 0.6),
                      (50.6, -4.0, 51.4, -2.6), (53.4, -2.9, 53.8, -1.5), (51.45, -0.3, 51.6, 0.15))
ORACLE_SG_TIMING = {"hours": 48.0, "points": 25, "gauges": 25, "per_gauge_ms": 0.3, "all_ms": 8.0, "factor": 3.0}

# The sensitivity tables (s6). Table 4: decay by distance, footprint 100 km, parameter
# 1.0; Table 5: the target by intensity and sensitivity for its test gauge; Table 6:
# k(1.0) at the defaults; Table 7: (1/2)^gamma; Table 8: the default storm by peak and
# gauge; Table 9: the time constants on the peak-100 crossing.
ORACLE_SG_T4 = {"distances": (0, 25, 50, 75, 100, 150, 200), "footprint": 100.0, "param": 1.0}
ORACLE_SG_T5 = {"intensities": (20, 40, 60, 80, 100),
                "gauge": {"base_level": 1.5, "flood_alert": 3.0, "flood_warning": 4.0,
                          "severe_warning": 5.0, "historical_high": 6.0}}
ORACLE_SG_T7_GAMMAS = ("0.5", "0.8", "1.0", "1.5")
