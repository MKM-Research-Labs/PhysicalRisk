# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Chart 2: Stress P&L — water level + stress P&L bars with knock-out."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the stress P&L chart."""
    return js_static('gauge/gaugehc/ghc_stress_charts/pnl.js')
