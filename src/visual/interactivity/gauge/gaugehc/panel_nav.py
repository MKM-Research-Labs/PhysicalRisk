# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel tab navigation — state vars, switchTab(), showPanel(), hidePanel()."""

from visual.interactivity._jsbundle import js_static


def get_nav_js() -> str:
    """Return JS for tab switching and panel show/hide."""
    return js_static('gauge/gaugehc/panel_nav.js')
