# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Chart 1: Flood Probability — water level + trigger levels + P(flood)."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the flood probability chart."""
    return js_static('gauge/gaugehc/ghc_stress_charts/probability.js')
