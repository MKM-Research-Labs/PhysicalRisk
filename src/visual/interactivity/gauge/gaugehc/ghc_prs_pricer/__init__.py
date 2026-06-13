# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Gauge hazard curve — PRS Pricing package.

Semi-annual cashflow computation (premium + protection legs),
fair spread calculation, and dual-chart layout (hazard curve + cashflow bars).
"""

from ._js import get_js

__all__ = ["get_js"]
