"""
Classifiers — detail sub-module.

Single-gauge detail panel: metrics grid + feature importance bar chart.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for the detail panel."""
    return js_static('trading/classifiers/detail.js')
