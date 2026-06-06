# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Control tab — data loading, saving, and reset logic."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for loadControlData / saveControlData / resetControlData."""
    return js_static('storm/sp_control/setup_data.js')
