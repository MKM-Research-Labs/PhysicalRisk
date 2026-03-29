# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Gauge hazard curve — PRS Pricing package.

Semi-annual cashflow computation (premium + protection legs),
fair spread calculation, and dual-chart layout (hazard curve + cashflow bars).
"""

from .engine import get_engine_js
from .renderer import get_renderer_js


def get_js() -> str:
    """Return JS fragment for PRS cashflow engine and chart rendering."""
    return get_engine_js() + get_renderer_js()
