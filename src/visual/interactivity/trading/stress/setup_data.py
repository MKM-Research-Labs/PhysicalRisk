# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress Test — data loading, gauge/storm dropdown population and handlers."""

from config.format import storm_option_js as _storm_opt

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for stress data loading and dropdown handlers."""
    return js_static('trading/stress/setup_data.js').replace(
        '__STORM_OPT__', _storm_opt('s', show_peak=True))
