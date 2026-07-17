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

"""Terrain grid, mortgage credit, and flood-poly model parameters."""

from typing import NamedTuple


# ===========================================================================
# Terrain Grid  (hazard/terrain_grid.py)
# ===========================================================================

# Elevation decay scale (metres).  At h = ELEV_SCALE_M the flood
# probability drops to 1/e of the gauge rate.  Thames corridor calibration.
ELEV_SCALE_M = 2.0

# Pricing parameters (fixed for grid — matches sensitivity tables)
GRID_TENOR = 5
GRID_RECOVERY = 0.0
GRID_RISK_FREE_RATE = 0.03

# ===========================================================================
# Mortgage Credit  (mortgage/pricer/credit.py)
# ===========================================================================

# Flood risk credit spread multipliers, keyed by normalised (title-case) category
FLOOD_RISK_MULTIPLIERS = {
    'Very Low': 1.00,
    'Low': 1.05,
    'Medium': 1.20,
    'High': 1.40,
    'Very High': 1.75,
}

# Fallbacks used when a loan record carries no per-loan value (decimals of
# property value / outstanding balance respectively).
LOAN_DEFAULT_INSURANCE_RATE = 0.002
LOAN_DEFAULT_RECOVERY_HAIRCUT = 0.20

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
