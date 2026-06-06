# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Leaflet map control button for opening the portfolio panel."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS for the Leaflet control button."""
    return js_static('storm/stormportfolio/control.js')
