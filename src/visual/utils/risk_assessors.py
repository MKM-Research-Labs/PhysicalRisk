# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Risk assessment utilities for the visualization system.

Analytical logic lives in models.risk.risk_assessor — this module
re-exports it and adds display helpers (colors, icons) that are
specific to the visualization layer.
"""


from models.risk.risk_assessor import RiskAssessor  # noqa: F401

from .color_schemes import ColorSchemes

# === Display helpers (visualization-only, not part of the model) ===

def get_risk_color(risk_level: str) -> str:
    """Folium marker name for a flood risk level.

    A marker name, not a hex colour: Leaflet markers take a name from a fixed
    vocabulary. The ramp lives in ``config.theme._status``.
    """
    return ColorSchemes.get_flood_risk_marker(risk_level)


def get_risk_icon(risk_level: str) -> str:
    """Get icon name for flood risk level."""
    risk_icons = {
        'Very Low': 'check-circle', 'Very low': 'check-circle',
        'Low': 'info-circle',
        'Medium': 'exclamation-triangle',
        'High': 'exclamation-circle',
        'Very High': 'times-circle', 'Very high': 'times-circle',
        'Unknown': 'question-circle'
    }
    return risk_icons.get(risk_level, 'question-circle')


def get_ltv_color(ltv_ratio: float) -> str:
    """Get color code for LTV ratio."""
    if ltv_ratio is None:
        return 'gray'
    if ltv_ratio > 1:
        ltv_ratio = ltv_ratio / 100
    if ltv_ratio <= 0.6:
        return 'green'
    elif ltv_ratio <= 0.8:
        return 'yellow'
    elif ltv_ratio <= 0.95:
        return 'orange'
    else:
        return 'red'


# Backward compatibility — keep class-level access working
RiskAssessor.get_risk_color = staticmethod(get_risk_color)
RiskAssessor.get_risk_icon = staticmethod(get_risk_icon)
RiskAssessor.get_ltv_color = staticmethod(get_ltv_color)


# Convenience functions for backward compatibility
def calculate_combined_risk(flood_risk: str, ltv_ratio: float) -> float:
    """Calculate combined risk score (backward compatibility)."""
    return RiskAssessor.calculate_combined_risk_score(flood_risk, ltv_ratio)
