# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Commercial Flood Time Series Generator.

A thin subclass of PropertyTimeSeriesGenerator with
``ASSET_CONFIG = COMMERCIAL_CONFIG``. All flood propagation, IDW
interpolation, depth-damage logic etc. is inherited unchanged from the
residential generator — only the input filename, JSON shape, and output
directory names differ.
"""

from port.src.property.ts import DateTimeEncoder, PropertyTimeSeriesGenerator  # noqa: F401
from port.utils.asset_config import COMMERCIAL_CONFIG


class CommercialTimeSeriesGenerator(PropertyTimeSeriesGenerator):
    """Commercial asset flood timeseries — reads commercial.json, writes
    commercialts/ (normal), commercialtsd/ (zero-elevation), or
    commercialtse/ (zero-distance) per-asset JSON files."""

    ASSET_CONFIG = COMMERCIAL_CONFIG


__all__ = ["CommercialTimeSeriesGenerator", "DateTimeEncoder"]
