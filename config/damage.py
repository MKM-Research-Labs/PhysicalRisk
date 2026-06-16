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
