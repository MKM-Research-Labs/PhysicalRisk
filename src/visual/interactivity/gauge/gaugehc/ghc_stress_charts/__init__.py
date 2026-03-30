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

from . import probability, pnl, surface


def get_js() -> str:
    """Return combined JS fragment for all stress test charts."""
    return (probability.get_js() +
            pnl.get_js() +
            surface.get_js())
