# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Portfolio and trading parameter registry.

All hard-coded parameters for the port pipeline and trading desk live here.
Source files import from this module rather than defining constants inline.

Subsections:
    Book / Trade Parameters     — port/src/book/book_common.py
    EOD Simulation              — port/src/historical_eod.py
    Delta Engine                — models/trading/delta_engine.py
    Market State                — models/trading/market_state.py
"""

from typing import Dict, List

# ===========================================================================
# Book / Trade Parameters  (port/src/book/book_common.py)
# ===========================================================================

# Available tenor lengths (years)
TENORS: List[int] = [1, 2, 3, 5]

# Available notional amounts (GBP)
NOTIONALS: List[int] = [5_000_000, 8_000_000, 10_000_000, 12_000_000, 20_000_000]

# Flood trigger levels used in book generation
TRIGGERS: List[str] = ['severe']

# Maps trigger name → hazard rate field name on the gauge hazard record
TRIGGER_RATE_KEY: Dict[str, str] = {
    'warning': 'annual_hazard_rate_warning',
    'severe':  'annual_hazard_rate_severe',
    'alert':   'annual_hazard_rate_alert',
}

# Recovery rate assumption for CDS-equivalent pricing (0 % = full LGD)
RECOVERY: float = 0.0

# Default yield curve: humped shape peaking at 4Y (matches market_state.py)
# Keys are tenor in years as strings; values are continuous rates.
DEFAULT_YIELD_CURVE: Dict[str, float] = {
    '1': 0.035,   # 3.5%
    '2': 0.040,   # 4.0%
    '3': 0.043,   # 4.3%
    '4': 0.045,   # 4.5%  ← peak
    '5': 0.040,   # 4.0%
    '6': 0.040,   # 4.0%
}

# Bid/ask spread construction: each side deviates SPREAD_OFFSET_MIN–SPREAD_OFFSET_MAX bp
# from fair value, giving a total bid-ask of 6–20 bp
SPREAD_OFFSET_MIN: float = 3.0    # bps
SPREAD_OFFSET_MAX: float = 10.0   # bps


# ===========================================================================
# EOD Simulation  (port/src/historical_eod.py)
# ===========================================================================

# Number of business days to simulate (~3 months of trading history)
NUM_BUSINESS_DAYS: int = 63

# Daily volatility for hazard curve random walk (2 bp/day)
DAILY_HAZARD_VOL: float = 0.0002

# Maximum cumulative drift from base rate across the simulation (20 bp)
MAX_TOTAL_MOVE: float = 0.0020


# ===========================================================================
# Delta Engine  (models/trading/delta_engine.py)
# ===========================================================================

# 1 basis-point bump used for numerical FS01 (Flood Sensitivity 01) calculation
BUMP_1BP: float = 0.0001


# ===========================================================================
# Stress / Flood Classifier  (models/stress/flood_classifier.py)
# ===========================================================================

# Storm horizon denominator for log-transform: ln((t+1) / LOG_END)
LOG_END: float = 168.0

# Epsilon for log-transform numerical stability
LOG_EPS: float = 1e-8

# Classifier feature-vector length (hours in a storm window)
NUM_CLASSIFIER_HOURS: int = 168

# Near-miss augmentation: synthetic sub-severe hydrographs per gauge
NEARMISS_COUNT: int = 200

# Near-miss peak range as fraction of severe level
NEARMISS_LOW: float = 0.80
NEARMISS_HIGH: float = 0.99

# ===========================================================================
# Synthetic Gauge Generator  (port/src/gauge/synthetic.py)
# ===========================================================================

# Merge synthetic gauges within this distance (metres) to avoid duplicates
SYNTH_DEDUP_DISTANCE_M: int = 50


# ===========================================================================
# Gauge Random Generator  (port/rand/thames/gauge/gauge_random.py)
# ===========================================================================

# Sampling weights for the 7 gauge technology types (must sum to 1.0)
GAUGE_TYPE_WEIGHTS: List[float] = [0.05, 0.05, 0.15, 0.10, 0.20, 0.25, 0.20]


# ===========================================================================
# Gaugets Random Generator  (port/rand/thames/gauge/gaugets_random.py)
# ===========================================================================

# Default simulation parameters for gaugets water-level generation
GAUGETS_SIM_PARAMS: Dict[str, object] = {
    "simulation_hours": 168,
    "time_step": 1,               # hours
    "flood_wave_speed": 1.5,      # gauges per hour (downstream propagation)
    "peak_flood_height_ratio": 2.5,    # ratio of peak height to flood alert level
    "initial_flood_height_ratio": 1.5,  # ratio of initial height to flood alert level
    "recession_rate": 0.02,       # metres per hour
    "peak_hour_min": 36,          # earliest hour when flood can peak
    "peak_hour_max": 84,          # latest hour when flood can peak
    "peak_hour_stagger": 2,       # hours between gauge peaks (downstream delay)
    "base_amplitude": 0.5,        # amplitude during normal conditions
    "peak_amplitude": 2.0,        # amplitude at flood peak
}


# ===========================================================================
# Mortgage Random Generator  (port/rand/thames/mortgage/constants.py)
# ===========================================================================

# Sampling weights for mortgage types: Residential / Buy-to-Let / Second Home /
# Holiday Home / Shared Ownership
MORTGAGE_TYPE_WEIGHTS: List[float] = [0.70, 0.15, 0.05, 0.05, 0.05]

# Sampling weights for rate types: Fixed / Variable / Tracker / Discount /
# Capped / Standard Variable Rate
RATE_TYPE_WEIGHTS: List[float] = [0.60, 0.10, 0.15, 0.05, 0.03, 0.07]


# ===========================================================================
# Property Hazard Curve  (port/src/property/hc/constants.py)
# ===========================================================================

# Flood depth thresholds for property-level hazard analysis (metres)
DEPTH_THRESHOLDS: Dict[str, float] = {
    'any_flood': 0.0,
    'moderate': 0.5,
    'severe': 1.0,
}

# Minimum flood events required to fit a GEV distribution
MIN_EVENTS_FOR_GEV: int = 3

# Maximum return period (years) — hazard curves are capped beyond this
MAX_RETURN_PERIOD: int = 100


# ===========================================================================
# EA Flood Zone — elevation boundaries (port/src/property/main/locations.py,
#                                        port/rand/thames/property/property_random.py)
# ===========================================================================

# Vertical offset above river level (metres).  Bounds are [lower, upper);
# upper=None means no upper limit.  Used by the property generator to derive
# the EA flood zone from the property's physical position.
EA_FLOOD_ZONE_ELEVATION_BOUNDS: Dict[str, tuple] = {
    'Zone 3b': (0.0, 0.5),    # Functional floodplain — at river level
    'Zone 3a': (0.5, 1.5),    # High probability — within typical flood depth
    'Zone 2':  (1.5, 3.0),    # Medium probability — above routine flooding
    'Zone 1':  (3.0, None),   # Low probability — well above flood levels
}


# ===========================================================================
# Property Timeseries  (port/src/property/ts/constants.py)
# ===========================================================================

# Number of nearest gauges used for IDW interpolation of flood levels
N_NEAREST_GAUGES: int = 3


# ===========================================================================
# Storm Multi — Event Window  (storm_multi/models/sequence_response.py,
#                               storm_multi/utils/validation.py)
# ===========================================================================

# Duration of the analysis window used for multi-storm sequences (hours = 7 days)
EVENT_WINDOW_HOURS: int = 168

# Minimum drainage tail required after last precipitation event (hours)
MIN_DRAINAGE_WINDOW_HOURS: int = 12


# ===========================================================================
# Storm Multi — Intensity Sampler  (storm_multi/generators/intensity_sampler.py)
# ===========================================================================

# Probability of a multi-storm sequence forming, by intensity category
SEQUENCE_PROBABILITY: Dict[str, float] = {
    "minimal": 0.05,
    "baseline": 0.15,
    "moderate": 0.30,
    "severe": 0.50,
    "extreme": 0.70,
    "catastrophic": 0.85,
}

# Default [doublet, cluster, persistent] weights for minimal/baseline categories
DEFAULT_TYPE_WEIGHTS: List[float] = [0.60, 0.30, 0.10]

# Intensity correlation within sequences (Spec Section 3.3)
INTENSITY_VARIATION: float = 0.20          # +/- 20% around base intensity
FIRST_STORM_DOMINANT_PROB: float = 0.30    # 30% chance first storm is strongest
CORRELATION_PROB: float = 0.70             # 70% chance subsequent storms >= first


# ===========================================================================
# Storm Multi — Batch Generator  (storm_multi/generators/batch_generator.py)
# ===========================================================================

# Default intensity category weights for batch generation (Spec Section 4.3)
DEFAULT_INTENSITY_WEIGHTS: Dict[str, float] = {
    "moderate": 0.40,
    "severe": 0.35,
    "extreme": 0.20,
    "catastrophic": 0.05,
}


# ===========================================================================
# Storm Multi — Sequence Generator  (storm_multi/generators/sequence_generator.py)
# ===========================================================================

# Base precipitation (mm) by catchment — used to scale storm intensity
CATCHMENT_BASE_PRECIP: Dict[str, float] = {
    "thames": 35.0,
    "rhine": 40.0,
    "danube": 45.0,
    "mississippi": 55.0,
}


# ===========================================================================
# Data Lineage  (lineage/manifest.py, routes/governance/lineage.py)
# ===========================================================================

# Chunk size for streaming SHA-256 file hashing (bytes)
LINEAGE_CHUNK_SIZE: int = 65536

# Pipeline staleness threshold — steps older than this are flagged (hours)
LINEAGE_STALE_HOURS: int = 72


# ===========================================================================
# Trading — Severity Ordering  (routes/trading/port_stress.py)
# ===========================================================================

# Sort key for gauge stress results (lower = more severe)
SEVERITY_ORDER: Dict[str, int] = {
    'severe': 0,
    'warning': 1,
    'alert': 2,
    'clean': 3,
}


# ===========================================================================
# Entity ID Naming Standards
# ===========================================================================
# Prefixes used when constructing STORM-xxx, GAUGE-xxx identifiers.
# All ID generators must read from these constants — never inline the prefix.

STORM_ID_PREFIX: str = "STORM"      # e.g. STORM-3f1a9c2b
GAUGE_ID_PREFIX: str = "GAUGE"      # e.g. GAUGE-0180833d
SEQUENCE_ID_PREFIX: str = "STORM"   # e.g. STORM-d0ef339e (unified prefix)


# ===========================================================================
# Stress Storms Catalogue  (port/src/gauge/stress_storms.py)
# ===========================================================================

# Minimum number of alert-breaching storms required in stress_storms.json
STRESS_STORMS_MIN_COUNT: int = 50

# Hydrograph defaults used when storm metadata is not stored in gaugets
STRESS_STORM_DEFAULT_DURATION_HOURS: int = 168
STRESS_STORM_DEFAULT_PEAK_POSITION: float = 0.5


# ===========================================================================
# Spatial Correlation Model  (storm_multi/models/spatial_correlation.py)
# ===========================================================================
# Thames-calibrated exponential correlation kernel (spec: Storm Generator
# Spatial Correlation Spec, Section 5 / Table 2).
# Previously persisted as data/input/thames/spatial_correlation.json.

# Spatial correlation switched on by default
SPATIAL_CORR_ENABLED: bool = True

# Kernel type — only "exponential" is implemented
SPATIAL_CORR_MODEL_TYPE: str = "exponential"

# Correlation range at intensity_factor = 1 (~half the Thames corridor, km)
SPATIAL_CORR_BASE_RANGE_KM: float = 40.0

# Nugget: micro-scale variability added to the diagonal (5%)
SPATIAL_CORR_NUGGET: float = 0.05

# Range scaling: range_km increases by rho_intensity per unit intensity_factor
# above 1, so extreme storms are more spatially coherent
SPATIAL_CORR_RHO_INTENSITY: float = 0.40

# Log-space standard deviation of the spatial precipitation field (40% CoV)
SPATIAL_CORR_SIGMA_LOGNORMAL: float = 0.40

# Default Thames gauge count — used as documentary metadata when writing
# spatial correlation config; the live model uses the actual gauge list
SPATIAL_CORR_NUM_GAUGES: int = 52
