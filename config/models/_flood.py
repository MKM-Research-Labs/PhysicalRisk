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

"""Risk thresholds, storm/PRS pricing, flood velocity and hydrograph params."""

from typing import Dict


# ===========================================================================
# Risk Assessment Thresholds  (models/risk/risk_assessor/)
# ===========================================================================

# Flood depth risk bands (metres) — used to classify property flood exposure
FLOOD_DEPTH_THRESHOLDS: Dict[str, float] = {
    'very_low': 0.0,
    'low': 0.1,
    'medium': 0.5,
    'high': 1.0,
    'very_high': 2.0,
}

# Loan-to-value risk bands — used to classify mortgage credit exposure
LTV_RISK_THRESHOLDS: Dict[str, float] = {
    'low': 0.6,
    'moderate': 0.8,
    'high': 0.95,
    'critical': 1.0,
}


# ===========================================================================
# Storm Simulation
# ===========================================================================

# Total simulation window in hours (168 = 7 days)
STORM_SIMULATION_HOURS: int = 168

# ===========================================================================
# PRS Pricing
# ===========================================================================

# Recovery rates by trigger level — 0 % = full loss given default
RECOVERY_RATES: Dict[str, float] = {
    'any_flood': 0.0,
    'moderate':  0.0,
    'severe':    0.0,
}

# Minimum PRS spread floor — FloodRE minimum insurance rate equivalent
MIN_PRS_SPREAD_BPS: float = 2.0

# EA Flood Zone representative annual hazard rates (midpoint of EA ranges)
EA_FLOOD_ZONE_RATES: Dict[str, float] = {
    'Zone 3b': 0.050,   # Functional floodplain
    'Zone 3a': 0.020,   # High (>1 in 100)
    'Zone 3':  0.020,   # High (generic)
    'Zone 2':  0.005,   # 1 in 100 to 1 in 1,000
    'Zone 1':  0.001,   # <1 in 1,000
}


# ===========================================================================
# Flood Velocity / Manning's Equation  (floodrisk/velocity.py)
# ===========================================================================

# Default Manning's roughness coefficient for urban floodplain
DEFAULT_ROUGHNESS: float = 0.04

# Terrain velocity scaling — relative to urban baseline (1.0).
# Lower values = slower flow = more attenuation on the floodplain.
# Higher values = faster flow = water reaches property with more energy.
# Based on Manning's n ratios: urban streets (n≈0.025) vs floodplain (n≈0.08).
# Velocity ∝ 1/n, so the ratio is n_urban / n_terrain.
TERRAIN_VELOCITY_SCALE: Dict[str, float] = {
    'urban':      1.0,    # Baseline — streets, hard surfaces (n≈0.025)
    'semi-urban': 0.7,    # Mixed — gardens, parks, some hard surface (n≈0.035)
    'rural':      0.5,    # Pasture, crops, soft ground (n≈0.050)
    'floodplain': 0.3,    # Heavy vegetation, wetland (n≈0.080)
}
DEFAULT_TERRAIN_TYPE: str = 'urban'

# Default retention length scale (meters).  Controls the exponential
# decay of peak WSE with distance from river.  At d = L the retention
# factor is 1/e ≈ 0.37; at d = 0 retention is 1.0 (full signal).
# 3 km e-folding length: at 600 m retention ≈ 0.82, at 2 km ≈ 0.51,
# at 5 km ≈ 0.19.  No near-field bypass — attenuation applies from 0 m.
DEFAULT_RETENTION_LENGTH: float = 10_000.0

# Minimum slope to avoid division instability
MIN_SLOPE: float = 0.001

# Default recession multiplier (drainage is slower than arrival)
DEFAULT_RECESSION_FACTOR: float = 1.5


# ===========================================================================
# Hydrograph Superposition v2.2  (floodrisk/hydrograph.py)
# ===========================================================================

# Gamma shape parameter α by sequence type.  Controls rise/fall balance:
# small α → fast rise, long tail (flashy); large α → broad symmetric peak.
HYDRO_ALPHA: Dict[str, float] = {
    'isolated':   0.3,
    'doublet':    0.3,
    'cluster':    0.7,
    'persistent': 1.0,
}

# Antecedent saturation: s_i = 1 + β × log(1 + A_i / P_0)
# β controls how much prior rainfall amplifies later peaks.
SATURATION_BETA: float = 0.2
SATURATION_P0_MM: float = 50.0

# Flow-path infiltration parameters
# κ: hourly rate at which flood water is absorbed along the path (1/hr)
INFILTRATION_RATE_PER_HOUR: float = 0.005
# Y_0: reference max infiltrable depth for fully pervious ground (m)
INFILTRATION_YMAX_REF_M: float = 0.10
# Default fraction impervious surface (urban Thames corridor)
DEFAULT_IMPERV_FRACTION: float = 0.4

# Superposition cap: max exceedance above base = factor × (severe − base).
# Prevents unrealistic compound peaks exceeding physical channel capacity.
SUPERPOSITION_CAP_FACTOR: float = 2.5
