# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Basis summary strip — populateBasisStrip() JS function."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS for the populateBasisStrip() function."""
    return js_static('property/propertyhc/panel_basis_strip.js')
