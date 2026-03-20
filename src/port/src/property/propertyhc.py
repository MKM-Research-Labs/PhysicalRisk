# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Backward-compatibility shim — import from port.src.property.hc instead."""

from .hc import *  # noqa: F401, F403
from .hc import (  # noqa: F401
    COMPOSITION_BASIS_BPS,
    DEPTH_THRESHOLDS,
    DISTANCE_MAX_BPS,
    ELEVATION_MAX_BENEFIT_BPS,
    MIN_ANNUAL_PROBABILITY,
    MIN_EVENTS_FOR_GEV,
    MIN_PRS_SPREAD_BPS,
    MODEL_UNCERTAINTY_BPS,
    RECOVERY_RATES,
    TERRAIN_BASIS_BPS,
    TENORS,
    PropertyHazardCurveGenerator,
)
