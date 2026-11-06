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

"""Wolfram oracle benchmark parameters for MKM-SP-001 (Spatial Interpolation Model).

The cases a benchmark run evaluates, the claims in SP-001's model document
(``spatial_model_v2.0.pdf``, 06-Nov-2026) it tests, and where it files its evidence.
v0.1 of the benchmark tested v1.0 (27-Mar-2026); it is kept, as evidence, at its commit.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_SP_MODULE = "models.floodrisk.spatial"
ORACLE_SP_SOURCES = ("src/models/floodrisk/spatial.py",)
ORACLE_SP_TESTS = ("tests/models/floodrisk/spatial.py", "tests/models/floodrisk/test_spatial_coverage.py")

ORACLE_SP_OUT_DIR = "docs/models/spatial_benchmark"
ORACLE_SP_DOC = "MKM-SP-001_wolfram_benchmark"
ORACLE_SP_CSV = "spatial.csv"
ORACLE_SP_WL = "spatial.wl"
ORACLE_SP_TABLE_PREFIX = "evidence_tables_"

# The code against the document's equations in double precision, distances in metres,
# and Wolfram against the 50-digit reference.
ORACLE_SP_CODE_TOL = 1e-12
ORACLE_SP_METRE_TOL = 1e-6
ORACLE_SP_WOLFRAM_TOL = 1e-25

# The document's constants: Eq. 1's radius (m), s3.2's default power and threshold (m).
ORACLE_SP_EARTH_R_M = 6371000
ORACLE_SP_POWER = 2
ORACLE_SP_MIN_DISTANCE_M = 1

# The cases. Gauges as (distance m, WSE m) for Eq. 2 at several powers; gauges as
# (lat, lon, elevation, depth) around a target for the lat/lon path; properties for
# Eq. 3 (lat, lon) with a length scale (m) and base correlation.
ORACLE_SP_IDW = (((500, 12.5), (2000, 11.8), (5000, 10.2)), ((100, 9.0), (100, 11.0)),
                 ((0.5, 7.0), (10, 3.0)), ((1.0, 4.0), (3.0, 6.0)), ((25000, 1.0),),
                 ((800, 5.5), (1200, 6.5), (3500, 4.0), (9000, 2.0)))
ORACLE_SP_POWERS = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
ORACLE_SP_TARGET = (51.5, -0.1)
ORACLE_SP_GAUGES = ((51.51, -0.1, 3.0, 1.2), (51.5, -0.088, 2.5, 0.8), (51.47, -0.15, 4.1, 0.3),
                    (51.55, -0.02, 1.9, 2.0))
ORACLE_SP_CORR_POINTS = ((51.5, -0.1), (51.5, -0.05), (51.55, -0.1), (51.52, -0.07), (51.6, 0.1))
ORACLE_SP_CORR = {"length_m": 2000.0, "base": 0.6}
ORACLE_SP_DEG_KM = 111.0

# The index (s3.3): one hand-made case -- a gauge 0.010 deg north and one 0.012 deg east
# of the target, which v1.0's degree index got wrong -- and seeded random networks over
# the Thames basin.
ORACLE_SP_TREE_CASE = {"target": (51.5, -0.1), "gauges": ((51.51, -0.1), (51.5, -0.088))}
ORACLE_SP_TREE_RANDOM = {"seed": 20261106, "networks": 20, "gauges": 50, "queries": 50,
                         "lat": (51.2, 51.8), "lon": (-1.0, 0.5)}

# The polyline projection (s3.5, Table 5): segments (lat, lon) -> (lat, lon), and points offset
# from their midpoints by these distances (km), north, east and north-west.
ORACLE_SP_SEGMENTS = (((51.5, -1.0), (51.5, 0.0)), ((51.0, -0.5), (52.0, -0.5)),
                      ((51.0, -1.0), (52.0, 0.5)), ((51.5, -0.1), (51.506, -0.09)))
ORACLE_SP_OFFSETS_KM = (0.01, 0.1, 1, 10, 50, 100, 200)
ORACLE_SP_FLAT_EARTH_KM = 50
ORACLE_SP_POLYLINE = ((51.50, -0.30), (51.51, -0.25), (51.49, -0.20), (51.505, -0.12), (51.50, -0.05))

# Claims, as v2.0 states them. s5: the sphere's worst error against WGS84 for UK pairs
# under 100 km (%); s3.4: the degree conversion overstates east-west separation at
# 51.5 N by this much (%); s3.3: the index's distance agrees with Eq. 1 to this
# relative error.
ORACLE_SP_SPHERE_STATED_PCT = 0.32
ORACLE_SP_EW_STATED = {"latitude": 51.5, "pct": 61}
ORACLE_SP_NEAREST_TOL = 1e-9
ORACLE_SP_UK_PAIRS = ((51.5, -1.0, 51.5, 0.3), (51.0, -0.3, 51.8, -0.3), (51.2, -1.4, 51.7, -0.6),
                      (50.6, -4.0, 51.0, -3.2), (53.4, -2.9, 53.7, -2.1), (51.45, -0.3, 51.6, 0.15))
# s2.2, Table 1: where the shared functions are used (the area under src/models or src/port/src).
ORACLE_SP_USED_BY = ("gauge", "property", "seismic")

# The tables (s6, Tables 2-5), as v2.0 prints them, and the cases they were generated from.
ORACLE_SP_T1 = {"base": ((500.0, 12.5), (2000.0, 11.8), (5000.0, 10.2)),
                "powers": (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)}
ORACLE_SP_T2_DISTANCES = (100, 250, 500, 1000, 2000, 5000, 10000)
ORACLE_SP_T3_GAUGES = ((500.0, 12.5), (1200.0, 12.0), (2000.0, 11.8), (3500.0, 11.0), (5000.0, 10.2))
ORACLE_SP_PRINTED_T1 = ("11.907", "12.200", "12.361", "12.438", "12.472", "12.487", "12.497")
ORACLE_SP_PRINTED_T2 = ("12.497", "12.484", "12.438", "12.293", "12.006", "11.691", "11.610")
ORACLE_SP_PRINTED_T3 = ("12.500", "12.426", "12.394", "12.372", "12.355")
# Table 5: the projection's worst error at each offset (km): per cent, and metres.
ORACLE_SP_PRINTED_T4 = ((10, "0.0000", "0.005"), (50, "0.0012", "0.608"), (100, "0.0049", "4.868"),
                        (200, "0.0195", "38.953"))
