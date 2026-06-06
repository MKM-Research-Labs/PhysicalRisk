# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — state variables and DOM creation (createVisView)."""

from visual.interactivity._jsbundle import js_static


def get_dom_js() -> str:
    """Return JS for Visual tab state vars and DOM builder."""
    return js_static('storm/sp_visual_dom.js')
