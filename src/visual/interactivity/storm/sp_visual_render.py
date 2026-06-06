# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — Chart.js multi-line chart rendering (renderSimChart)."""

from visual.interactivity._jsbundle import js_static


def get_render_js() -> str:
    """Return JS for the renderSimChart function."""
    return js_static('storm/sp_visual_render.js')
