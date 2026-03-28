# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Property hazard curve generator — hc package."""

from .constants import (  # noqa: F401
    DEPTH_THRESHOLDS,
    MIN_ANNUAL_PROBABILITY,
    MIN_EVENTS_FOR_GEV,
    MIN_PRS_SPREAD_BPS,
    RECOVERY_RATES,
    TENORS,
)
from .generator import PropertyHazardCurveGenerator  # noqa: F401

__all__ = [
    "PropertyHazardCurveGenerator",
    "DEPTH_THRESHOLDS",
    "MIN_ANNUAL_PROBABILITY",
    "MIN_EVENTS_FOR_GEV",
    "MIN_PRS_SPREAD_BPS",
    "RECOVERY_RATES",
    "TENORS",
]
