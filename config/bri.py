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

"""
BRI (Building Resilience Index) parameters.

All BRI-related calibration lives here:
    Damage-stilt shift     — flood depth-damage BRI adjustment (depth_damage.py)
    Floor-level uplift      — BRI-adjusted flood threshold (depth_damage.py)
    v_50 shift              — wind BRI adjustment (winddamage/bri_shift.py)
    Shared numerical floor  — ln() guard for the log-uplift terms
    Resilience defaults     — property-resilience model + synthetic generator
"""

from typing import Dict


# ===========================================================================
# BRI Adjustment — flood  (Building Resilience Index → effective depth stilt)
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

# Reference composite BRI score (log base-point). Reused by the wind shift below.
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


# ===========================================================================
# Shared numerical floor for the BRI log-uplift terms
# ===========================================================================

# Small floor to prevent ln(0) in the BRI log-uplift terms; scores at or below
# this are treated as effectively zero. Shared by the flood and wind BRI shifts.
LN_FLOOR: float = 1e-6


# ===========================================================================
# Property-resilience model + synthetic-generator defaults
# ===========================================================================

# Default 0-1 compliance for a missing resilience value
# (spec recommends 0.25 + a confidence penalty).
DEFAULT_MISSING_COMPLIANCE: float = 0.25

# Synthetic property-resilience generation fallbacks: flood-defence adoption
# probability for an unknown construction period, and the condition multiplier
# for an unknown building condition.
RESILIENCE_DEFAULT_PERIOD_PROB: float = 0.40
RESILIENCE_DEFAULT_CONDITION_MULT: float = 1.0
