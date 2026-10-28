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

"""Wolfram oracle benchmark parameters for MKM-SEIS-001 (Building Seismic-Resilience Credit).

The assets a benchmark run prices, the claims in SEIS-001's model document
(``seismic_resilience.pdf`` v0.10) it tests, and where it files its evidence. The
document's sensitivity tables are in ``_wolfram_oracle_seis_tables``.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_SEIS_PACKAGE = "models.seismic"
ORACLE_SEIS_SOURCES = ("src/models/seismic/damage.py", "src/models/seismic/groundmotion.py",
                       "src/models/seismic/responseeffectiveness.py",
                       "src/models/seismic/occurrence/_rates.py",
                       "src/models/seismic/occurrence/_simulate.py")

ORACLE_SEIS_OUT_DIR = "docs/models/seismic_resilience_benchmark"
ORACLE_SEIS_DOC = "MKM-SEIS-001_wolfram_benchmark"
ORACLE_SEIS_CSV = "seismic.csv"
ORACLE_SEIS_WL = "seismic.wl"
ORACLE_SEIS_TABLE_PREFIX = "evidence_tables_"

ORACLE_SEIS_MODEL_ID = "MKM-SEIS-001"
ORACLE_SEIS_MODEL_NAME = "Building Seismic-Resilience Credit Model"

# The document's sensitivity generator (removed from the repo in 527b5a348): its draw
# count, seed and geometry -- a short E-W fault at latitude 21.0, with each asset due
# south of its midpoint, so that every clipped rupture covers the perpendicular foot
# and R_JB is the asset's offset.
ORACLE_SEIS_N_SIM = 20_000
ORACLE_SEIS_SEED = 20260608
ORACLE_SEIS_FAULT = ((106.00, 21.0), (106.02, 21.0))      # [lon, lat] vertices
ORACLE_SEIS_FAULT_LAT = 21.0
ORACLE_SEIS_FAULT_LON = 106.01
ORACLE_SEIS_KM_PER_DEG = 111.0                            # the generator's placement
ORACLE_SEIS_EARTH_RADIUS_KM = 6371.0                      # the code's haversine
ORACLE_SEIS_PRODUCTION_N_SIM = 10_000                     # config.seismic SeismicRunConfig

# The generator's baseline: a 4-storey office, RC pre-code, stiff soil (450 m/s),
# Moderate zone, 20 km from the fault, no BRI measures.
ORACLE_SEIS_BASELINE = {
    "asset_id": "C-SEIS-BASE", "commercial_type": "Office", "construction_type": "RC_PreCode",
    "number_of_storeys": 4, "soil_vs30_mps": 450.0, "seismic_hazard_class": "Medium",
    "property_condition": "Fair", "measures": (), "r_jb_km": 20.0,
}
# Its BRI positions (cumulative) and measure sets.
_B = ("GS01", "GS05", "GS07", "GS10", "GS11", "GS14")
_A = _B + ("GS02", "GS08", "GS09", "GS15", "GS16")
ORACLE_SEIS_BRI = {"NR": (), "B": _B, "A": _A,
                   "AA": _A + ("GS03", "GS12", "GS13", "GS17", "GS18")}

ORACLE_SEIS_REL_TOL = 1e-12
ORACLE_SEIS_Z_LIMIT = 4.0
# NIntegrate's precision goal for Wolfram's integrals over magnitude.
ORACLE_SEIS_WOLFRAM_GOAL = 25
ORACLE_SEIS_WOLFRAM_TOL = 1e-20

# The document's claims, tested as stated:
#   Table 2   the six acceptance gates; the near-zero floor below 1 bp at
#             (Very low, R_JB = 100 km);
#   s9.6      "stability is adequate at n_sim = 20,000";
#   Table 18  "Mean L" of 0.01 / 0.10 / 0.35 for DS0-DS2, "truncated-lognormal".
ORACLE_SEIS_CLAIM_FLOOR_BPS = 1.0
ORACLE_SEIS_FLOOR_CELL = {"seismic_hazard_class": "None", "r_jb_km": 100.0}
ORACLE_SEIS_CLAIM_MEAN_LOSS = {"DS0": 0.01, "DS1": 0.10, "DS2": 0.35}
# s9.6 "stability is adequate": read here as a relative standard error of the spread
# at most this, wherever the exact spread is at least 1 bp.
ORACLE_SEIS_STABLE_REL_SE = 0.10
