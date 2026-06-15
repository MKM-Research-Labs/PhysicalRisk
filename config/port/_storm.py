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

"""Portfolio/trading parameter registry — split submodule. See config.port."""

from typing import Dict, List


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
    'Zone 3b': (None, 0.5),   # Functional floodplain — at or below river level (lo unbounded)
    'Zone 3a': (0.5, 1.5),    # High probability — within typical flood depth
    'Zone 2':  (1.5, 3.0),    # Medium probability — above routine flooding
    'Zone 1':  (3.0, None),   # Low probability — well above flood levels
}


# ===========================================================================
# Flood Propagation  (port/src/property/ts/flood/propagation.py)
# ===========================================================================

# Bankfull offset below severe warning level (metres).  Overbank flooding
# begins at bankfull, not at the severe warning threshold.  The severe
# level is an administrative safety alert set 0.5-1.0m above bankfull
# for UK rivers.  See: EA Flood Warning Data Integrity Guide v2.0.
BANKFULL_OFFSET_M: float = 0.5


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
# Storm <-> Typhoon Coupling  (docs/models/storm_typhoon_coupling/coupling_spec.md)
# ===========================================================================

# Coupling-strength knob beta for the directed-asymmetric storm->wind map (§4).
# The wind percentile floor is f(q) = 1 - (1-q)^beta, the ceiling is q, and
# rho_w = f(q) + B*(q - f(q)), B~Uniform[0,1]; Vmax = S_cat^-1(1 - rho_w).
#   beta -> 0  : pure ceiling, no tail pull (wind only bounded above by severity)
#   beta = 1   : deterministic comonotone (wind percentile == severity quantile)
#   beta ~ 0.52: fits the expert anchors (90th-pct storm -> 70th-pct wind floor,
#                99th -> 90th).
# Calibration is an open work item (coupling_spec.md §10); ship the documented
# default and expose --coupling-beta for the planned PRS sensitivity study.
COUPLING_BETA: float = 0.5


# ===========================================================================
# Storm Multi — Sequence Generator
# ===========================================================================
#
# Per-catchment base precipitation (mm) now lives in
# data/catch/<catchment>/storm.py as ``BASE_PRECIPITATION_MM``. Loaded
# at runtime by storm_multi.generators.sequence_generator.
