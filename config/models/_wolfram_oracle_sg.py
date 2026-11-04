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
(``storm_gauge.pdf`` v1.3, 11-Mar-2026, as filed) it tests, and where it files its
evidence.
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

# The document's constants: Eqs. 1-2's radius, Eq. 13's exponent, Eq. 16's rise
# multiplier, Table 3's defaults and Table 2's default stages (multiples of the alert).
ORACLE_SG_EARTH_R_KM = 6371
ORACLE_SG_GAMMA = "0.8"
ORACLE_SG_RISE = 3
ORACLE_SG_DT, ORACLE_SG_LAG, ORACLE_SG_DECAY = 0.5, 2.0, 12.0
ORACLE_SG_STAGES = {"base": 0.35, "warning": 1.33, "severe": 1.58, "high_of_severe": 1.1}
ORACLE_SG_ALERT = 4.0

# The cases. A default storm (Table 1: 24 h, 25 track points, footprint 40 km,
# triangular, Gaussian 0.5) crossing the Thames west to east; gauges on its track and
# north of it; the other kernels and profiles; and settings that exercise the floor in
# Eq. 15 and a duration that is not a whole number of steps.
ORACLE_SG_TRACK = ((-1.0, 51.5), (0.5, 51.5))
ORACLE_SG_GAUGE = (-0.25, 51.5)
ORACLE_SG_OFFSETS_DEG = (0.0, 0.1, 0.2, 0.4)
ORACLE_SG_PEAKS = (30.0, 50.0, 80.0, 100.0)
ORACLE_SG_SETTINGS = ((0.5, 2.0, 12.0), (0.25, 2.0, 12.0), (1.0, 3.3, 6.0), (0.5, 2.0, 24.0))
ORACLE_SG_DURATIONS = (24.0, 23.7, 48.0)

# Claims. s6.2: a +-25% change in gamma moves a mid-range contribution by 20-25%;
# s3.5: the intensities that bring the level to alert, warning, severe and the
# historical high; s3.7 and s7.1: peak level follows peak intensity by about tau_lag;
# s8(5): the sphere is within 0.3% of the ellipsoid at UK scale; Q3: timings.
ORACLE_SG_GAMMA_SHIFT, ORACLE_SG_GAMMA_STATED = 0.25, (0.20, 0.25)
ORACLE_SG_TARGETS = {"alert": 40.0, "warning": (60.0, 70.0), "severe": 85.0, "high": 100.0}
ORACLE_SG_TARGET_TOL = 5.0
ORACLE_SG_LAG_TOL_H = 0.5
ORACLE_SG_ELLIPSOID_PCT = 0.3
ORACLE_SG_UK_PAIRS = ((51.5, -1.0, 51.5, 0.5), (51.0, -0.3, 52.8, -0.3), (51.2, -1.4, 52.1, 0.6),
                      (50.6, -4.0, 51.4, -2.6), (53.4, -2.9, 53.8, -1.5), (51.45, -0.3, 51.6, 0.15))
ORACLE_SG_TIMING = {"hours": 48.0, "points": 25, "gauges": 25, "per_gauge_ms": 10.0, "all_ms": 250.0}

# The printed sensitivity tables (s6). Table 4: decay by distance, footprint 100 km,
# parameter 1.0; Table 5: contribution by scale and intensity for its test gauge;
# Table 6: k(1.0) at the defaults; Table 7: (1/2)^gamma.
ORACLE_SG_T4 = {"distances": (0, 25, 50, 75, 100, 150, 200), "footprint": 100.0, "param": 1.0}
ORACLE_SG_PRINTED_T4 = (("1.00", "1.00", "1.00"), ("0.9692", "0.7788", "0.7500"),
                        ("0.8825", "0.6065", "0.5000"), ("0.7548", "0.4724", "0.2500"),
                        ("0.6065", "0.3679", "0.0000"), ("0.3247", "0.2231", "0.0000"),
                        ("0.1353", "0.1353", "0.0000"))
ORACLE_SG_T5 = {"scales": (0.05, 0.08, 0.10, 0.12, 0.15, 0.20), "intensities": (20, 40, 60, 80, 100),
                "gauge": {"base_level": 1.5, "flood_alert": 3.0, "flood_warning": 4.0,
                          "severe_warning": 5.0, "historical_high": 6.0}}
ORACLE_SG_PRINTED_T5 = ("1.24", "2.16", "2.99", "3.76", "4.50")
ORACLE_SG_PRINTED_T6 = ("0.135", "0.135", "0.0")
ORACLE_SG_T7_GAMMAS = ("0.5", "0.8", "1.0", "1.5")
ORACLE_SG_PRINTED_T7 = ("0.707", "0.574", "0.500", "0.354")
ORACLE_SG_PRINTED_GAUSS = ("60.7", "13.5")      # s3.3.1: % of on-track intensity at sigma, 2 sigma
