# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Panel DOM construction — createPanel() JS function."""

from visual.interactivity._jsbundle import js_static


def get_create_panel_js() -> str:
    """Return JS that defines the createPanel() function."""
    return js_static('gauge/gaugehc/panel_create.js')
