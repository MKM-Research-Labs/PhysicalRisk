# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PRS Pricing renderer — cashflow table, hazard curve chart, stats bar."""

from visual.interactivity._jsbundle import js_static


def get_renderer_js() -> str:
    """Return JS for renderPRSPricing."""
    return js_static('gauge/gaugehc/ghc_prs_pricer/renderer.js')
