# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Stress Test — chart tab switching and drawing dispatch."""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for stress chart tab switching."""
    return js_static('trading/stress/setup_charts.js')
