# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress P&L chart — bar chart with water level overlay."""

from visual.interactivity._jsbundle import js_static


def get_pnl_chart_js() -> str:
    """Return JS for _tdRenderStressPnlChart."""
    return js_static('trading/stress/charts/pnl.js')
