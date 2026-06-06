# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Tab 3: P(flood) Surface Table — heat-map grid of probabilities."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the P(flood) surface table."""
    return js_static('gauge/gaugehc/ghc_stress_charts/surface.js')
