# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — data loading and stats rendering."""

from visual.interactivity._jsbundle import js_static


def get_data_js() -> str:
    """Return JS for storm label lookup, loadSimData, and renderSimStats."""
    return js_static('storm/sp_visual_data.js')
