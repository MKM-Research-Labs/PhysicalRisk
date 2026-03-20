# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Module-level constants for property hazard curve generation."""

from config.port import DEPTH_THRESHOLDS, MAX_RETURN_PERIOD, MIN_EVENTS_FOR_GEV  # noqa: F401
from models.hazard.prs_analytical import (  # noqa: F401
    COMPOSITION_BASIS_BPS,
    DISTANCE_CAP_KM,
    DISTANCE_MAX_BPS,
    DISTANCE_RATE_BPS_PER_KM,
    ELEVATION_MAX_BENEFIT_BPS,
    ELEVATION_RATE_BPS_PER_M,
    MIN_PRS_SPREAD_BPS,
    MODEL_UNCERTAINTY_BPS,
    RECOVERY_RATES,
    TERRAIN_BASIS_BPS,
    compute_basis_waterfall,
    compute_prs_spread,
)

# DEPTH_THRESHOLDS, MIN_EVENTS_FOR_GEV, MAX_RETURN_PERIOD imported from config/port.py

# Tenors for term structure
TENORS = [1, 2, 3, 4, 5]

MIN_ANNUAL_PROBABILITY = 1.0 / MAX_RETURN_PERIOD  # 0.01
