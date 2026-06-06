"""
Classifiers — training sub-module.

Single-gauge training (POST + poll), batch Train All with progress bar.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for training controls and progress."""
    return js_static('trading/classifiers/training.js')
