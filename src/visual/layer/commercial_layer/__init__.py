# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Commercial asset layer for the visualization system.

Adds commercial-asset markers (office / multifamily / hotel / retail /
mixed-use / etc.) to the Folium map. Each marker uses a distinct icon
per CommercialType and a purple colour palette to distinguish from the
residential layer (which is green/orange/red by flood frequency).

Sub-modules:
- layer: CommercialLayer class
- popup: commercial marker popup HTML
- stats: per-type counts + total valuation
"""

from .layer import CommercialLayer  # noqa: F401
from .popup import create_commercial_popup  # noqa: F401
from .stats import get_commercial_statistics  # noqa: F401

__all__ = [
    "CommercialLayer",
    "create_commercial_popup",
    "get_commercial_statistics",
]
