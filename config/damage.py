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
Depth-damage model parameters.

All calibration constants for models/floodrisk/depth_damage.py live here.
Subsections:
    Vulnerability Curve        — piecewise-linear depth → damage ratio
    Property Type Factors      — damage multipliers by occupancy class
    Spatial / Flood Geometry   — Thames reference point and distance decay
    BRI Adjustment             — building resilience index damage reduction
"""

from typing import Dict, List

# ===========================================================================
# Vulnerability Curve  (UK-calibrated, JBA / MCM lineage)
# ===========================================================================

# Control points for the piecewise-linear depth-damage curve.
# depth (m above floor level) → damage ratio [0, 1].
# Calibrated to UK residential flood loss data.
DEPTH_POINTS:  List[float] = [0, 0.05, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0]
DAMAGE_POINTS: List[float] = [0, 0.05, 0.25, 0.40, 0.50, 0.60, 0.75, 0.85, 0.95, 1.0]


# ===========================================================================
# Property Type Damage Factors
# ===========================================================================

# Multiplicative adjustments to the base vulnerability curve by occupancy.
# residential = 1.0 baseline; commercial contents are more exposed at low
# depths; industrial typically has raised plant and more durable finishes.
PROPERTY_TYPE_DAMAGE_FACTORS: Dict[str, float] = {
    'residential': 1.0,
    'commercial':  1.2,
    'industrial':  0.9,
}


# ===========================================================================
# Spatial / Flood Geometry
# ===========================================================================

# Maximum distance from a property's controlling (synthetic) gauge at which
# flood influence is non-zero (m).  Beyond this the depth is set to zero.
FLOOD_MAX_DISTANCE_M: float = 25_000.0

# Hard cap on computed flood depth (m).
# Prevents physically implausible values from propagating to the damage model.
FLOOD_DEPTH_CAP_M: float = 5.0

# Fallback elevation (m AOD) when a property record lacks an elevation field.
DEFAULT_ELEVATION_M: float = 20.0


# ===========================================================================
# Depth-Damage Polynomial  (calibrated to vulnerability curve above)
# ===========================================================================

# Degree-5 polynomial fitted to DEPTH_POINTS / DAMAGE_POINTS.
# Constrained to pass through the origin (f(0) = 0 exactly).
# Monotone increasing on [0, 6] — verified at calibration time.
#
#   damage(h) = c1·h + c2·h² + c3·h³ + c4·h⁴ + c5·h⁵
#
# Fit quality (origin-constrained, n=10 control points):
#   R²      = 0.999244
#   RMSE    = 0.009368
#   MaxErr  = 0.020388  (at h = 0.05 m)
#   f(6)    = 1.001  (clipped to 1.0 at runtime)
DD_POLY_COEFFS: List[float] = [
    +0.60573746,   # h^1
    -0.27377812,   # h^2
    +0.08114485,   # h^3
    -0.01191896,   # h^4
    +0.00066130,   # h^5
]

# ===========================================================================
# BRI Adjustment  (Building Resilience Index → effective depth stilt)
# ===========================================================================
#
# The BRI stilt shifts the effective flood depth before it enters the damage
# polynomial.  A positive stilt reduces damage (property is hardened); a
# negative stilt increases it (property is more vulnerable than the baseline).
#
#   stilt = BRI_FLOOD_ALPHA_M · ln(bri_flood / BRI_FLOOD_REFERENCE)
#         + BRI_COMPOSITE_BETA_M · ln(bri_composite / BRI_COMPOSITE_REFERENCE)
#
#   effective_depth = max(0,  raw_depth  −  floor_level  −  stilt)
#   damage          = poly(effective_depth)
#
# The stilt is fully signed — no clamp.  Below-reference properties get a
# negative stilt (higher effective depth, more damage).  The max(0, …) is
# only applied to effective_depth, which is a physical identity.
#
# All four scalar parameters should be recalibrated once loss data is
# available.  The reference scores default to 0.50 (neutral mid-point);
# replace with portfolio weighted means at deployment.

# Sensitivity of stilt to the flood sub-score (metres per ln-unit).
# Captures physical flood-proofing: barriers, tanking, raised thresholds.
BRI_FLOOD_ALPHA_M: float = 0.40

# Sensitivity of stilt to the composite BRI score (metres per ln-unit).
# Captures systemic resilience: fabric quality, maintenance, structural integrity.
BRI_COMPOSITE_BETA_M: float = 0.20

# Reference flood sub-score (log base-point — stilt is zero at this value).
# Update to portfolio weighted mean of BRIFloodScore when live data is available.
BRI_FLOOD_REFERENCE: float = 0.50

# Reference composite BRI score (log base-point).
# Update to portfolio weighted mean of BRIScore when live data is available.
BRI_COMPOSITE_REFERENCE: float = 0.50

# Hard cap on stilt magnitude (metres).  Prevents extreme log values at very
# high BRI scores from producing physically implausible depth reductions.
BRI_STILT_MAX_M: float = 1.00


# ===========================================================================
# BRI Adjusted Floor Level  (Building Resilience Index → effective floor uplift)
# ===========================================================================
#
# A separate, coarser mechanism from the depth-damage stilt above. Where the
# stilt nudges the damage curve, the floor uplift raises the *flood threshold*
# used by the PRS event filter: a highly-resilient building (raised thresholds,
# barriers, flood-proof construction) only counts as flooded once the water
# rises well above its nominal floor.
#
#   adjusted_floor = FloorLevelMeters + uplift(BRIFloodScore)
#   floods         ⟺  attenuated_wse_m > GroundLevelMeters + adjusted_floor
#
# The uplift is a continuous, monotone ramp in the BRI flood sub-score, anchored
# on the grade thresholds:
#   • score ≤ SCORE_LO (NR band)  → +0 m   (no resilience credit)
#   • score ≥ SCORE_HI (AA band)  → +MAX_M (full resilience credit)
#   • linear in between
#
# This is deliberately additive (a credit on top of the surveyed floor level),
# never subtractive: a poor BRI score cannot lower the threshold below the
# physical floor. The damage-curve stilt above remains the channel for
# below-reference vulnerability.
#
# Recalibrate MAX_M against post-event resilience performance when loss data
# is available; the anchors track the BRIFloodScore grade bands.

# Maximum floor-level uplift (metres) awarded at / above the AA anchor score.
BRI_FLOOR_UPLIFT_MAX_M: float = 3.00

# BRI flood sub-score at / below which no uplift is awarded (NR / B boundary).
BRI_FLOOR_UPLIFT_SCORE_LO: float = 0.38

# BRI flood sub-score at / above which the full uplift is awarded (AA anchor).
BRI_FLOOR_UPLIFT_SCORE_HI: float = 0.87

# Representative BRIFloodScore for each BRI letter grade. Used only when an
# asset carries a letter rating but no numeric flood score — e.g. commercial
# assets, whose flood resilience is recorded as a Water/Flash grade envelope
# rather than the residential 0-1 BRIFloodScore. Each value is the mid-point of
# that grade's score band (see RATING_THRESHOLDS in the rand resilience module:
# AA ≥ 0.87, A ≥ 0.62, B ≥ 0.38, NR < 0.38), so the continuous uplift curve is
# evaluated at a sensible point for the grade.
BRI_FLOOR_RATING_SCORES: Dict[str, float] = {
    "AA": 0.935,   # mid-point of [0.87, 1.00]
    "A":  0.745,   # mid-point of [0.62, 0.87]
    "B":  0.500,   # mid-point of [0.38, 0.62]
    "NR": 0.190,   # mid-point of [0.00, 0.38]
}


# ===========================================================================
# Wind Vulnerability  (peak sustained wind → damage ratio, sigmoid form)
# ===========================================================================
#
# Mirrors the flood architecture: a pure curve plus a BRI-aware wrapper.
# The wind curve is a piecewise saturated sigmoid centred on v_50:
#
#   DR(v) = 1 / (1 + exp(-a * (v - v_50)))
#
# where v is the peak sustained wind at the property during an event
# (m/s) and v_50 is the wind speed at which 50% damage is realised.
#
# v_50 resolution rule (consumers — not enforced here):
#   1. property carries CDM field WindThresholdKph → v_50 = ../3.6
#   2. else use WIND_V50_BASE_MS as fallback
#   3. then layer the BRI shift on top (next section)

# Sigmoid steepness in per-m/s. At a = 0.20 the curve moves from ~10% to
# ~90% damage over a 22 m/s span — sharp transition appropriate for the
# structural-damage threshold of a typical building.
WIND_SIGMOID_A_PER_MS: float = 0.20

# Fallback v_50 in m/s when a property has no WindThresholdKph field.
# 27.8 m/s = 100 km/h — a conservative default for residential structures.
WIND_V50_BASE_MS: float = 27.8

# Property-side fallback in km/h. Used by threshold resolution code so
# the unit conversion stays in one place.
DEFAULT_WIND_THRESHOLD_KPH: float = 100.0


# ===========================================================================
# BRI Adjustment — wind  (Building Resilience Index → v_50 shift)
# ===========================================================================
#
# Mirrors the flood-side BRI stilt. A positive shift translates the
# damage curve rightward (less damage at the same gust); a negative
# shift translates it left (more damage). The shift is in m/s.
#
#   shift = BRI_WIND_ALPHA_MS     · ln(bri_wind      / BRI_WIND_REFERENCE)
#         + BRI_COMPOSITE_BETA_MS · ln(bri_composite / BRI_COMPOSITE_REFERENCE)
#
#   v_50_eff = v_50 + shift,   clamped to ±WIND_V50_SHIFT_MAX_MS
#
# All four scalar parameters should be recalibrated once loss data is
# available. BRI_COMPOSITE_REFERENCE is reused from the flood section.

# Sensitivity of the v_50 shift to the wind sub-score (m/s per ln-unit).
# Captures wind-specific hardening: glazing standards, roof attachment,
# cladding rating.
BRI_WIND_ALPHA_MS: float = 6.0

# Sensitivity of the v_50 shift to the composite BRI score (m/s per ln-unit).
# Captures systemic resilience: fabric quality, maintenance, structural integrity.
BRI_COMPOSITE_BETA_MS: float = 3.0

# Reference wind sub-score (log base-point — shift is zero at this value).
# Update to portfolio weighted mean of BRIWindScore when live data is available.
BRI_WIND_REFERENCE: float = 0.50

# Hard cap on v_50 shift magnitude (m/s). Prevents extreme log values at
# very high BRI scores from producing implausible damage reductions.
WIND_V50_SHIFT_MAX_MS: float = 12.0
