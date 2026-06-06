# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""sp_visual — gauge visibility toggle functions and outside-click listener."""

from visual.interactivity._jsbundle import js_static


def get_toggle_js() -> str:
    """Return JS for toggleGaugeVisibility, toggleAllGauges, updateGaugeBtnLabel."""
    return js_static('storm/sp_visual_toggle.js')
