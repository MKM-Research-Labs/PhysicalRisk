# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Gauge hazard curve — Stress Test charts package.

Sub-modules:
- probability: Chart 1 — Flood Probability (water level + triggers + P(flood))
- pnl: Chart 2 — Stress P&L (water level + P&L bars)
- surface: Tab 3 — P(flood) surface heat-map table
"""

from ._js import get_js

__all__ = ["get_js"]
