# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Shared JS utilities: formatting helpers, color functions."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS for shared utility functions."""
    return js_static('storm/stormportfolio/utilities.js')
