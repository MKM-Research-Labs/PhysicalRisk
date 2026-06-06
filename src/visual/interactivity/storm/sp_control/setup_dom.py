# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Control tab — DOM construction for the storm control view."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for createControlView() DOM builder."""
    return js_static('storm/sp_control/setup_dom.js')
