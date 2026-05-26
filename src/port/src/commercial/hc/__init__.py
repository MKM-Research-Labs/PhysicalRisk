# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Commercial Hazard Curve Generator.

A thin subclass of PropertyHazardCurveGenerator with
``ASSET_CONFIG = COMMERCIAL_CONFIG``. Reads the commercial timeseries
output (commercialts/, commercialtsd/, commercialtse/) and writes
commercialhc.json / commercialshd.json / commercialshe.json.

PRS pricing, basis calculation, and spread decomposition are inherited
unchanged from the residential generator.
"""

from port.src.property.hc import (  # noqa: F401
    DEPTH_THRESHOLDS,
    MIN_ANNUAL_PROBABILITY,
    MIN_EVENTS_FOR_GEV,
    MIN_PRS_SPREAD_BPS,
    RECOVERY_RATES,
    TENORS,
    PropertyHazardCurveGenerator,
)
from port.utils.asset_config import COMMERCIAL_CONFIG


class CommercialHazardCurveGenerator(PropertyHazardCurveGenerator):
    """Commercial hazard curves, PRS pricing, basis, and spread
    decomposition. Inherits all behaviour from the residential generator
    via ASSET_CONFIG."""

    ASSET_CONFIG = COMMERCIAL_CONFIG


__all__ = [
    "CommercialHazardCurveGenerator",
    "DEPTH_THRESHOLDS",
    "MIN_ANNUAL_PROBABILITY",
    "MIN_EVENTS_FOR_GEV",
    "MIN_PRS_SPREAD_BPS",
    "RECOVERY_RATES",
    "TENORS",
]
