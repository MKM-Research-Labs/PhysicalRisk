# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial hazard-curve generator (CPROP-* assets)."""

from port.src.property.hc import PropertyHazardCurveGenerator
from port.utils.asset_config import COMMERCIAL_CONFIG


class CommercialHazardCurveGenerator(PropertyHazardCurveGenerator):
    """Commercial hazard curves, PRS pricing, basis, and spread
    decomposition. Inherits all behaviour from the residential generator
    via ASSET_CONFIG."""

    ASSET_CONFIG = COMMERCIAL_CONFIG
