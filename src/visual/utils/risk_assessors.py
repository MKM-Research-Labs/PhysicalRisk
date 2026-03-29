# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

# === Display helpers (visualization-only, not part of the model) ===

def get_risk_color(risk_level: str) -> str:
    """Get color code for flood risk level."""
    risk_colors = {
        'Very Low': 'green', 'Very low': 'green',
        'Low': 'lightgreen',
        'Medium': 'orange',
        'High': 'red',
        'Very High': 'darkred', 'Very high': 'darkred',
        'Unknown': 'blue',
        'N/A': 'gray'
    }
    return risk_colors.get(risk_level, 'blue')


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
def assess_mortgage_risk_summary(flood_risk_level: str, mortgage_value: float,
                               loan_amount: float, ltv_ratio: float) -> str:
    """Generate mortgage risk summary (backward compatibility)."""
    return RiskAssessor.assess_mortgage_risk(
        flood_risk_level, mortgage_value, loan_amount, ltv_ratio
    )

def calculate_combined_risk(flood_risk: str, ltv_ratio: float) -> float:
    """Calculate combined risk score (backward compatibility)."""
    return RiskAssessor.calculate_combined_risk_score(flood_risk, ltv_ratio)
