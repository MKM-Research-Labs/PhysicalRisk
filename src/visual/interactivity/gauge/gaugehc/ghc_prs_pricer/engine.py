# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PRS Analytical Pricer — semi-annual cashflow computation."""

from visual.interactivity._jsbundle import js_static


def get_engine_js() -> str:
    """Return JS for computePRSCashflows."""
    return js_static('gauge/gaugehc/ghc_prs_pricer/engine.js')
