# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""P(flood) Surface Table — heatmap-style HTML table."""

from visual.interactivity._jsbundle import js_static


def get_surface_table_js() -> str:
    """Return JS for _tdRenderSurfaceTable."""
    return js_static('trading/stress/charts/surface.js')
