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
Model parameter registry.

All hard-coded analytical parameters for the MKM model library live here.
Grouped by model subsystem. Model source files import from this module
rather than defining constants inline.

Subsections:
    PRS Basis Waterfall       — prs_analytical.py
    Depth-Damage Curve        — floodrisk/depth_damage.py
    Flood Velocity / Manning  — floodrisk/velocity.py
    Property Valuation        — valuation/property_value.py
    Insurance Premium         — valuation/insurance.py
"""

from typing import Dict, List, Tuple, NamedTuple

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
# PRS Basis Waterfall  (PRS Property Pricing Spec v1.0)
# ===========================================================================

# Fixed model uncertainty spread (bps)
MODEL_UNCERTAINTY_BPS: float = 2.0

# Terrain variation by EA flood zone (Spec Section 4.4)
TERRAIN_BASIS_BPS: Dict[str, float] = {
    'Zone 3b':          3.0,
    'Zone 3a':          3.0,
    'Zone 3':           3.0,
    'Zone 2':           2.0,
    'Zone 1':           0.0,
    'Enhanced Defence': -1.0,
}

# Property composition adjustment by type (Spec Table 3)
COMPOSITION_BASIS_BPS: Dict[str, float] = {
    'Flat':           2.0,
    'Bungalow':       1.0,
    'Mid-terrace':    0.5,
    'End-terrace':    0.5,
    'Semi-detached':  0.0,
    'Detached':       0.0,
}

# Construction year cutoff — pre-2000 buildings attract +1 bp
CONSTRUCTION_YEAR_CUTOFF: int = 2000

# Distance basis: min(DISTANCE_MAX_BPS, DISTANCE_RATE_BPS_PER_KM × d_weighted_km)
# capped at DISTANCE_CAP_KM km
DISTANCE_RATE_BPS_PER_KM: float = 0.5
DISTANCE_MAX_BPS:          float = 6.0
DISTANCE_CAP_KM:           float = 12.0

# Elevation basis: max(-ELEVATION_MAX_BENEFIT_BPS, -ELEVATION_RATE_BPS_PER_M × Δh)
# only applies when property is above gauge; else 0
ELEVATION_RATE_BPS_PER_M:   float = 0.2
ELEVATION_MAX_BENEFIT_BPS:  float = 3.0

# Recovery rates by trigger level — 0 % = full loss given default
RECOVERY_RATES: Dict[str, float] = {
    'any_flood': 0.0,
    'moderate':  0.0,
    'severe':    0.0,
}

# Minimum PRS spread floor — FloodRE minimum insurance rate equivalent
MIN_PRS_SPREAD_BPS: float = 2.0


# ===========================================================================
# Depth-Damage Curve  (UK-calibrated, floodrisk/depth_damage.py)
# ===========================================================================

# Control points for piecewise-linear depth-damage vulnerability curve
DEPTH_POINTS:  List[float] = [0, 0.05, 0.5, 1, 1.5, 2, 3, 4, 5, 6]
DAMAGE_POINTS: List[float] = [0, 0.05, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.95, 1.0]


# ===========================================================================
# Flood Velocity / Manning's Equation  (floodrisk/velocity.py)
# ===========================================================================

# Default Manning's roughness coefficient for urban floodplain
DEFAULT_ROUGHNESS: float = 0.04

# Default retention length scale (meters).  Controls the exponential
# decay of peak WSE with distance from river.  At d = L the retention
# factor is 1/e ≈ 0.37; at d = 0 retention is 1.0 (full signal).
# 3 km e-folding length: at 600 m retention ≈ 0.82, at 2 km ≈ 0.51,
# at 5 km ≈ 0.19.  No near-field bypass — attenuation applies from 0 m.
DEFAULT_RETENTION_LENGTH: float = 3_000.0

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


# ===========================================================================
# Property Valuation  (valuation/property_value.py)
# ===========================================================================

# Floor area ranges by property type (sq metres)
BASE_AREA_RANGES: Dict[str, Tuple[float, float]] = {
    'Flat':           (35,  120),
    'Mid-terrace':    (60,  180),
    'End-terrace':    (70,  200),
    'Semi-detached':  (80,  250),
    'Detached':       (120, 400),
    'Bungalow':       (80,  200),
}

# Base price per square metre by property type (London averages, GBP)
BASE_PRICE_PER_SQM: Dict[str, Tuple[float, float]] = {
    'Detached':      (8000,  15000),
    'Semi-detached': (6500,  12000),
    'Mid-terrace':   (6000,  11000),
    'End-terrace':   (6200,  11500),
    'Bungalow':      (7000,  13000),
    'Flat':          (5500,  10000),
}

# Age band adjustment factors (construction_year → factor range)
AGE_BAND_FACTORS: Dict[str, Tuple[float, float]] = {
    'new_build':   (1.05, 1.15),   # < 10 years
    'modern':      (0.95, 1.05),   # 10–24 years
    'established': (0.90, 1.00),   # 25–49 years
    'period':      (0.85, 0.95),   # 50–99 years
    'heritage':    (0.80, 1.20),   # 100+ years
}

# Condition adjustment factors
CONDITION_FACTORS: Dict[str, Tuple[float, float]] = {
    'Excellent': (1.10, 1.20),
    'Good':      (1.00, 1.10),
    'Fair':      (0.90, 1.00),
    'Poor':      (0.70, 0.90),
    'Very poor': (0.50, 0.70),
}

# Flood-risk discount / premium factors on property value
FLOOD_RISK_FACTORS: Dict[str, Tuple[float, float]] = {
    'Very Low':  (1.00, 1.02),
    'Low':       (0.98, 1.00),
    'Medium':    (0.92, 0.98),
    'High':      (0.85, 0.92),
    'Very High': (0.75, 0.85),
}

# EPC rating adjustment factors
EPC_FACTORS: Dict[str, Tuple[float, float]] = {
    'A': (1.05, 1.10),
    'B': (1.02, 1.05),
    'C': (1.00, 1.02),
    'D': (0.98, 1.00),
    'E': (0.95, 0.98),
    'F': (0.90, 0.95),
    'G': (0.85, 0.90),
}

# Thames proximity factors (distance band × flood-risk category)
PROXIMITY_ZONES: Dict[str, Dict[str, Tuple[float, float]]] = {
    'close_low_risk':  {'range': (1.05, 1.15)},   # < 200 m, low flood risk
    'close_high_risk': {'range': (0.90, 1.05)},   # < 200 m, medium+ flood risk
    'medium':          {'range': (0.95, 1.10)},   # 200–500 m
    'far':             {'range': (0.98, 1.02)},   # > 500 m
}

# Rental yield rates by property type (annual gross yield)
RENTAL_YIELD_RATES: Dict[str, Tuple[float, float]] = {
    'Flat':           (0.04,  0.07),
    'Mid-terrace':    (0.045, 0.065),
    'End-terrace':    (0.045, 0.065),
    'Semi-detached':  (0.04,  0.06),
    'Detached':       (0.035, 0.055),
    'Bungalow':       (0.04,  0.06),
}

# Rent per sqm by property type (GBP / month)
RENT_PER_SQM: Dict[str, Tuple[float, float]] = {
    'Flat':           (25, 50),
    'Mid-terrace':    (20, 40),
    'End-terrace':    (22, 42),
    'Semi-detached':  (18, 35),
    'Detached':       (15, 30),
    'Bungalow':       (18, 35),
}

# Property value bounds (London market)
MIN_PROPERTY_VALUE: int = 150_000
MAX_PROPERTY_VALUE: int = 5_000_000


# ===========================================================================
# Insurance Premium  (valuation/insurance.py)
# ===========================================================================

# Property type base premium multipliers
PROPERTY_TYPE_PREMIUM_FACTORS: Dict[str, Tuple[float, float]] = {
    'Flat':           (0.80, 1.00),
    'Mid-terrace':    (0.90, 1.10),
    'End-terrace':    (1.00, 1.20),
    'Semi-detached':  (1.10, 1.30),
    'Detached':       (1.20, 1.50),
    'Bungalow':       (1.00, 1.20),
}

# Flood-risk premium multipliers
FLOOD_RISK_PREMIUM_FACTORS: Dict[str, Tuple[float, float]] = {
    'Very Low':  (0.90, 1.00),
    'Low':       (1.00, 1.20),
    'Medium':    (1.30, 1.80),
    'High':      (1.80, 2.50),
    'Very High': (2.50, 4.00),
}

# Construction age premium factors
AGE_PREMIUM_FACTORS: Dict[str, Tuple[float, float]] = {
    'new_build':   (0.80, 0.90),   # < 10 years
    'modern':      (0.90, 1.00),   # 10–29 years
    'established': (1.00, 1.30),   # 30–99 years
    'heritage':    (1.20, 1.80),   # 100+ years
}

# Construction type premium factors
CONSTRUCTION_TYPE_FACTORS: Dict[str, Tuple[float, float]] = {
    'Brick':          (0.90, 1.00),
    'Stone':          (0.90, 1.00),
    'Concrete':       (0.95, 1.05),
    'Timber Frame':   (1.10, 1.30),
    'Modern methods': (0.85, 0.95),
}

# Floor-area premium bands: (upper_bound_sqm, (min_factor, max_factor))
AREA_PREMIUM_BANDS: List[Tuple[float, Tuple[float, float]]] = [
    (50,          (0.90, 1.00)),
    (100,         (1.00, 1.10)),
    (200,         (1.10, 1.20)),
    (float('inf'), (1.20, 1.40)),
]

# Base rate range (GBP per GBP 1,000 of property value)
BASE_RATE_RANGE: Tuple[float, float] = (1.5, 4.0)

# Annual premium bounds (GBP)
MIN_PREMIUM: int = 200
MAX_PREMIUM: int = 20_000


# ===========================================================================
# Flood Poly — Polynomial Flood Probability Model  (models/stress/flood_poly.py)
# ===========================================================================
# Logistic sigmoid fitted to the GBM classifier surface (GAUGE-dc5e88fb).
# P(flood) = σ(a·h + b·t + c·h·t + d·h² + e·t² + f)
# where h = ln(w/s), t = ln((hour+1)/T).


class FloodPolyCoeffs(NamedTuple):
    """Sigmoid polynomial coefficients for p_flood_poly."""
    a: float   # log water level (h)
    b: float   # log time (t)
    c: float   # h·t interaction
    d: float   # h² quadratic
    e: float   # t² quadratic
    f: float   # intercept


flood_poly_coeffs = FloodPolyCoeffs(
    a=28.9582,
    b=-11.6351,
    c=26.5490,
    d=-22.8893,
    e=-7.0794,
    f=-0.8872,
)

# Storm horizon for log-time normalisation (hours)
flood_poly_storm_hours: int = 168

# Floor for log transform to avoid ln(0)
flood_poly_log_eps: float = 1e-8

# Exponent clamp to prevent overflow in sigmoid
flood_poly_exp_clamp: float = 30.0

# Fit quality metrics (documentary — not used at runtime)
flood_poly_fit = {
    "model_id": "flood-poly-v1",
    "version": "1.0.0",
    "r_squared": 0.9395,
    "mae": 0.0456,
    "rmse": 0.0986,
    "source_gauge": "GAUGE-dc5e88fb",
    "source_auc": 0.9939,
    "source_samples": 3_393_600,
}
