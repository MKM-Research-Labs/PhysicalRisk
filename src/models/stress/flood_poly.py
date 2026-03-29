# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package root __init__.py for full license text)

"""
Polynomial Flood Probability Model (FloodPoly)
===============================================

Model type:  Logistic sigmoid with quadratic polynomial kernel
Model ID:    flood-poly-v1
Fitted from: GBM classifier (GAUGE-dc5e88fb, AUC=0.994, 3.4M samples)
Fit method:  Nonlinear least-squares (scipy.optimize.curve_fit)

Overview
--------
A closed-form approximation of the per-gauge GBM flood classifier.
Replaces the need for trained ``.joblib`` model files and scikit-learn
at inference time.  The model operates entirely in log-transformed
feature space, which normalises water levels across gauges with
different severe thresholds.

Features (2)
------------
  h = ln(w / s)           — log water level relative to severe threshold
  t = ln((hour + 1) / T)  — log normalised storm time (T = 168 hours)

Both features are gauge-independent: ``h = 0`` when water equals the
severe level; ``t = 0`` at the final storm hour.

Model equation
--------------
  P(flood) = σ(a·h + b·t + c·h·t + d·h² + e·t² + f)

where σ is the standard logistic function 1/(1 + exp(-z)).

All coefficients and parameters are defined in ``config/models.py``
under the FloodPoly section.

Performance vs GBM classifier
------------------------------
  R²  = 0.94
  MAE = 0.046
  RMSE = 0.099

The model is conservative: it slightly over-predicts P(flood) in the
transition zone (alert → severe) and slightly under-predicts at the
tails.  This is acceptable for stress testing where false negatives
are costlier than false positives.

Usage
-----
Single-gauge hourly stress (scenario.py):
    ``p = p_flood_poly(water_level=5.2, hour=48, severe_level=6.58)``

Portfolio stress (port_stress.py) — time-independent variant:
    ``p = p_flood_simple(water_level=5.2, severe_level=6.58)``
"""

import math
from typing import List, Tuple

from config.models import (
    flood_poly_coeffs,
    flood_poly_storm_hours,
    flood_poly_log_eps,
    flood_poly_exp_clamp,
    flood_poly_fit,
)


# ---------------------------------------------------------------------------
# Core model functions
# ---------------------------------------------------------------------------

def _log_features(water_level: float, hour: int,
                  severe_level: float) -> Tuple[float, float]:
    """Transform raw inputs to log-space features.

    Returns:
        (h, t) where h = ln(w/s) and t = ln((hour+1)/T).
    """
    h = math.log(max(water_level / severe_level, flood_poly_log_eps))
    t = math.log((hour + 1) / flood_poly_storm_hours)
    return h, t


def _sigmoid(z: float) -> float:
    """Logistic sigmoid with overflow protection."""
    z = max(-flood_poly_exp_clamp, min(flood_poly_exp_clamp, z))
    return 1.0 / (1.0 + math.exp(-z))


def p_flood_poly(water_level: float, hour: int,
                 severe_level: float) -> float:
    """Estimate P(flood) from water level, storm hour, and severe threshold.

    This is the full 2D model using both log(w/s) and log(t/T).
    Use for single-gauge hourly stress scenarios where the time
    dimension matters.

    Args:
        water_level: Current water level in metres AOD.
        hour: Storm hour index (0 = start, 167 = end).
        severe_level: Severe flood warning threshold in metres AOD.

    Returns:
        Probability between 0 and 1.
    """
    if severe_level <= 0:
        return 0.0
    a, b, c, d, e, f = flood_poly_coeffs
    h, t = _log_features(water_level, hour, severe_level)
    z = a * h + b * t + c * h * t + d * h**2 + e * t**2 + f
    return _sigmoid(z)


def p_flood_simple(water_level: float, severe_level: float) -> float:
    """Time-independent P(flood) for portfolio stress.

    Uses the ratio of water level to severe threshold, capped at 1.0.
    Suitable for portfolio-level stress where only peak water level
    is available (no hourly dimension).

    Args:
        water_level: Peak water level in metres AOD.
        severe_level: Severe flood warning threshold in metres AOD.

    Returns:
        Probability between 0 and 1.
    """
    if severe_level <= 0:
        return 0.0
    return min(1.0, water_level / severe_level)


def p_flood_series(water_levels: List[float],
                   severe_level: float) -> List[float]:
    """Compute P(flood) for an hourly hydrograph.

    Convenience wrapper over ``p_flood_poly`` for a full time series.

    Args:
        water_levels: Hourly water levels (length <= storm_hours).
        severe_level: Severe flood warning threshold in metres AOD.

    Returns:
        List of probabilities, same length as water_levels.
    """
    return [
        p_flood_poly(wl, h, severe_level)
        for h, wl in enumerate(water_levels)
    ]


# ---------------------------------------------------------------------------
# Model metadata (for audit / reporting)
# ---------------------------------------------------------------------------

def model_card() -> dict:
    """Return model metadata for audit and documentation."""
    return {
        "model_id": flood_poly_fit["model_id"],
        "version": flood_poly_fit["version"],
        "type": "logistic_sigmoid_polynomial",
        "features": ["ln(w/s)", "ln((t+1)/T)"],
        "num_parameters": len(flood_poly_coeffs),
        "coefficients": {
            "a (log_h_s)": flood_poly_coeffs.a,
            "b (log_t)": flood_poly_coeffs.b,
            "c (h*t interaction)": flood_poly_coeffs.c,
            "d (h² quadratic)": flood_poly_coeffs.d,
            "e (t² quadratic)": flood_poly_coeffs.e,
            "f (intercept)": flood_poly_coeffs.f,
        },
        "fitted_from": {
            "source_model": "GradientBoostingClassifier",
            "source_gauge": flood_poly_fit["source_gauge"],
            "source_auc": flood_poly_fit["source_auc"],
            "source_samples": flood_poly_fit["source_samples"],
        },
        "fit_quality": {
            "r_squared": flood_poly_fit["r_squared"],
            "mae": flood_poly_fit["mae"],
            "rmse": flood_poly_fit["rmse"],
        },
        "storm_hours": flood_poly_storm_hours,
    }
