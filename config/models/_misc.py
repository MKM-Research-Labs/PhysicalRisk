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
# v2.0 (MKM-FPO-001): P = 1 at or above the severe level; below it
# P(flood) = σ(Σ c·h^i·t^j) over flood_poly_terms, h = ln(w/s) held at the level
# floor, t = ln((hour+1)/T). Fitted by tools/flood_poly_fit to every gauge's GBM on
# real storm states, pooled; v1.0 was a quadratic fitted to GAUGE-dc5e88fb alone.
flood_poly_coeffs = (32.871867, -12.801048, -7.540193, 44.826451, -2.848226, 54.512653, -0.756589, -29.568283, 6.254275, -1.29381)

# Storm horizon for log-time normalisation (hours)
flood_poly_storm_hours: int = 168

# Exponent clamp to prevent overflow in sigmoid
flood_poly_exp_clamp: float = 30.0

# v2.0 kernel: z = sum_k c_k h^i t^j over these (i, j), cubic in (h, t).
flood_poly_terms = ((1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (3, 0), (0, 3), (2, 1), (1, 2), (0, 0))

# The v2.0 fit (tools/flood_poly_fit): storms per gauge drawn once with this seed;
# states at or above this fraction of severe weigh more; the monotone penalty and
# the grid of levels (from this fraction of severe up to it) and hours it holds.
flood_poly_fit_storms: int = 2000
flood_poly_fit_seed: int = 7
flood_poly_fit_near: float = 0.75
flood_poly_fit_near_weight: float = 5.0
flood_poly_fit_penalty: float = 1e8
flood_poly_fit_grid = (0.2, 120)
flood_poly_fit_slope_margin: float = 0.01     # dz/dh held at least this, so rounding cannot undo it
# The optimiser's ftol/xtol/gtol. At scipy's default (1e-8) the fit stopped on a
# plateau: on synthetic data it failed to recover a kernel it was shown.
flood_poly_fit_tol: float = 1e-15
flood_poly_fit_max_evals: int = 5000

# Below this fraction of severe the v2.0 model holds its value there (effectively
# zero), so the constraint above it makes P non-decreasing in the level everywhere.
flood_poly_level_floor: float = 0.2

# The support envelope: (fraction of severe, earliest storm hour) at which any
# gauge's storms first reached that level -- 2000 storms per gauge, all 11 gauges.
# No storm rises faster, so the GBMs have never been shown a state before this hour
# and the fitted kernel there is extrapolation. The model holds the hour at the
# envelope (interpolated linearly in log-time between knots): a level reached
# earlier than any storm reached it is priced as the earliest storm that did.
# Below the first knot every hour is supported.
flood_poly_envelope = ((0.326, 0.0), (0.35, 2.3), (0.4, 4.7), (0.45, 6.1), (0.5, 7.5),
                       (0.55, 8.9), (0.6, 10.8), (0.65, 12.9), (0.7, 15.1), (0.75, 18.4),
                       (0.8, 22.0), (0.85, 24.9), (0.9, 29.3), (0.95, 35.7), (1.0, 37.4))
# Points per envelope segment at which the fit holds P rising along it.
flood_poly_fit_envelope_points: int = 20

# Fit quality metrics (documentary — not used at runtime)
flood_poly_fit = {
    "model_id": "flood-poly-v2",
    "version": "2.0.0",
    "fitted_to": {"source_model": "GradientBoostingClassifier (MKM-FC-001)", "gauges": 11,
                  "storms_per_gauge": 2000, "fit_states": 1807233,
                  "test_states": 1807896},
    # On held-out storms, near severe (w/s >= 0.75), across the gauges.
    "fit_quality": {"near_mae": (0.0408, 0.0658),
                    "near_bias": (-0.0343, 0.0247),
                    "below_mae": (0.0064, 0.0203)},
}
