# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial flood time-series generator (CPROP-* assets)."""

from port.src.property.ts import PropertyTimeSeriesGenerator
from port.utils.asset_config import COMMERCIAL_CONFIG


class CommercialTimeSeriesGenerator(PropertyTimeSeriesGenerator):
    """Commercial asset flood timeseries — reads commercial.json, writes
    commercialts/ (normal), commercialtsd/ (zero-elevation), or
    commercialtse/ (zero-distance) per-asset JSON files."""

    ASSET_CONFIG = COMMERCIAL_CONFIG
