# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Module-level constants for property hazard curve generation."""

from config.port import DEPTH_THRESHOLDS, MIN_EVENTS_FOR_GEV  # noqa: F401
from models.hazard.prs_analytical import (  # noqa: F401
    MIN_PRS_SPREAD_BPS,
    RECOVERY_RATES,
    compute_prs_spread,
)

# DEPTH_THRESHOLDS, MIN_EVENTS_FOR_GEV imported from config/port.py

# Tenors for term structure
TENORS = [1, 2, 3, 4, 5]

# Minimum annual probability derived from the 2bp spread floor (MIN_PRS_SPREAD_BPS).
# Previously derived from MAX_RETURN_PERIOD (a display parameter for gauge
# return period charts), which incorrectly imposed a 1% floor that capped
# all properties to 101bp and flattened the spread decomposition.
MIN_ANNUAL_PROBABILITY = MIN_PRS_SPREAD_BPS / 10_000  # 0.0002
