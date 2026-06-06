"""
Classifiers — setup sub-module.

State variables, DOM construction, data loading.
Sub-modules imported and concatenated here.
"""

from visual.interactivity._jsbundle import js_static

from . import summary_table, detail, training


def get_js() -> str:
    """Return JavaScript fragment for the full Classifiers tab (Tab 9)."""
    return (
        _get_setup_js()
        + summary_table.get_js()
        + detail.get_js()
        + training.get_js()
    )


def _get_setup_js() -> str:
    """Return JavaScript for state, DOM, and data loading."""
    return js_static('trading/classifiers/setup.js')
