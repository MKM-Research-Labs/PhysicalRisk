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

"""Wolfram oracle benchmark parameters for MKM-FIRE-001 (Building Fire-Resilience Credit).

The assets a benchmark run prices, the claims in FIRE-001's model document
(``fire_resilience.pdf`` v0.40) it tests, and where it files its evidence. The
document's sensitivity tables are in ``_wolfram_oracle_fire_tables``. Shared
settings -- kernel, precision -- are in ``_wolfram_oracle``.
"""

# The code under test, imported as production imports it (config puts src/ on the path).
ORACLE_FIRE_PACKAGE = "models.fire"
ORACLE_FIRE_SOURCES = ("src/models/fire/containment.py",
                       "src/models/fire/intensity_track.py",
                       "src/models/fire/response_effectiveness.py",
                       "src/models/fire/initiation.py")

ORACLE_FIRE_OUT_DIR = "docs/models/fire_resilience_benchmark"
ORACLE_FIRE_DOC = "MKM-FIRE-001_wolfram_benchmark"
ORACLE_FIRE_CSV = "fire.csv"
ORACLE_FIRE_WL = "fire.wl"
ORACLE_FIRE_TABLE_PREFIX = "evidence_tables_"

ORACLE_FIRE_MODEL_ID = "MKM-FIRE-001"
ORACLE_FIRE_MODEL_NAME = "Building Fire-Resilience Credit Model"

# The document's sensitivity generator (removed from the repo in 527b5a348): its
# draw count and seed, so the model's run reproduces the printed tables.
ORACLE_FIRE_N_SIM = 20_000
ORACLE_FIRE_SEED = 20260606
# The draw count production runs at (config.fire FireRunConfig), for the spread's
# sampling error as the Commercial PRS Pricer quotes it.
ORACLE_FIRE_PRODUCTION_N_SIM = 1_000

# The generator's baseline: a fully-occupied 3-storey office in Fair condition with
# every resilience field at Meets minimum (construction unset, so the default
# combustibility applies).
ORACLE_FIRE_LEVELS = ("Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified")
ORACLE_FIRE_BASELINE = {
    "asset_id": "C-SENS-BASE", "commercial_type": "Office",
    "occupancy_status": "Fully occupied", "business_rates_category": None,
    "property_condition": "Fair", "fire_damage_severity": None,
    "years_since_last_fire": None, "number_of_storeys": 3,
    **{f"{field}_level": "Meets minimum" for field in (
        "automatic_detection", "suppression_systems", "emergency_procedures",
        "structural_fire_resistance", "compartments", "fire_stopping",
        "external_materials", "access_route", "business_continuity")},
}

# Model C against its documented formulae; the exact credit, Wolfram against the
# reference; and the model's Monte Carlo against the exact credit, in standard errors.
ORACLE_FIRE_REL_TOL = 1e-12
ORACLE_FIRE_Z_LIMIT = 4.0

# The document's other claims, tested as stated:
#   s7.1  the chain march absorbs in about 3 steps on average (baseline);
#   s7.1  latent intensity climbs about 0.8 per step (baseline);
#   T12   a non-combustible frame with no effective suppression realises a sub-bp
#         residual, single-digit bps "in very tall non-combustible assets".
ORACLE_FIRE_CLAIM_ABSORB_STEPS = 3.0
ORACLE_FIRE_CLAIM_GROWTH = 0.8
ORACLE_FIRE_CLAIM_RESIDUAL_BPS = 1.0
ORACLE_FIRE_TALL_STOREYS = 20
