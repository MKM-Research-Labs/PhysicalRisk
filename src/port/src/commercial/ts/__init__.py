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

from port.src.property.ts import DateTimeEncoder  # noqa: F401
from ._generator import CommercialTimeSeriesGenerator

__all__ = ["CommercialTimeSeriesGenerator", "DateTimeEncoder"]
