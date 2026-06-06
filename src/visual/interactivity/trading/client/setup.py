# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Client tab — setup sub-module.

State variables, DOM construction, and data loading for property PRS trades.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript fragment for client tab state, DOM, and loading."""
    return js_static('trading/client/setup.js')
