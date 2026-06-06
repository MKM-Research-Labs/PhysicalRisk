# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flood Probability chart — dual-axis water level + P(flood) %."""

from visual.interactivity._jsbundle import js_static


def get_probability_chart_js() -> str:
    """Return JS for _tdRenderProbabilityChart."""
    return js_static('trading/stress/charts/probability.js')
