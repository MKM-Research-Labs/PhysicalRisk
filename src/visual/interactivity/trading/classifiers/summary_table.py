"""
Classifiers — summary table sub-module.

Renders the all-gauge table with status, metrics, and train/retrain buttons.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JavaScript for the summary table."""
    return js_static('trading/classifiers/summary_table.js')
