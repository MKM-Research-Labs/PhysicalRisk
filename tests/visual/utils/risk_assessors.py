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
Tests for visual.utils.risk_assessors.

Covers: get_risk_color, get_risk_icon, get_ltv_color, and the backward-
compat convenience functions assess_mortgage_risk_summary and
calculate_combined_risk.
"""

import pytest

from visual.utils.risk_assessors import (
    get_risk_color,
    get_risk_icon,
    get_ltv_color,
    assess_mortgage_risk_summary,
    calculate_combined_risk,
)


# ===========================================================================
# get_risk_color
# ===========================================================================

class TestGetRiskColor:

    @pytest.mark.parametrize("level,expected", [
        ("Very Low", "green"),
        ("Very low", "green"),
        ("Low", "lightgreen"),
        ("Medium", "orange"),
        ("High", "red"),
        ("Very High", "darkred"),
        ("Very high", "darkred"),
        ("Unknown", "blue"),
        ("N/A", "gray"),
    ])
    def test_known_levels(self, level, expected):
        assert get_risk_color(level) == expected

    def test_unrecognised_level_returns_blue(self):
        assert get_risk_color("Catastrophic") == "blue"

    def test_returns_string(self):
        assert isinstance(get_risk_color("High"), str)


# ===========================================================================
# get_risk_icon
# ===========================================================================

class TestGetRiskIcon:

    @pytest.mark.parametrize("level,expected", [
        ("Very Low", "check-circle"),
        ("Very low", "check-circle"),
        ("Low", "info-circle"),
        ("Medium", "exclamation-triangle"),
        ("High", "exclamation-circle"),
        ("Very High", "times-circle"),
        ("Very high", "times-circle"),
        ("Unknown", "question-circle"),
    ])
    def test_known_levels(self, level, expected):
        assert get_risk_icon(level) == expected

    def test_unrecognised_level_returns_question_circle(self):
        assert get_risk_icon("Enormous") == "question-circle"

    def test_returns_string(self):
        assert isinstance(get_risk_icon("Medium"), str)


# ===========================================================================
# get_ltv_color
# ===========================================================================

class TestGetLTVColor:

    def test_none_returns_gray(self):
        assert get_ltv_color(None) == "gray"

    def test_low_ltv_green(self):
        assert get_ltv_color(0.5) == "green"

    def test_boundary_60_is_green(self):
        assert get_ltv_color(0.60) == "green"

    def test_medium_ltv_yellow(self):
        assert get_ltv_color(0.75) == "yellow"

    def test_high_ltv_orange(self):
        assert get_ltv_color(0.85) == "orange"

    def test_very_high_ltv_red(self):
        assert get_ltv_color(0.98) == "red"

    def test_percentage_normalised(self):
        # 80% > 1 → normalised to 0.80
        assert get_ltv_color(80) == get_ltv_color(0.80)

    def test_150_percent_is_red(self):
        # 150 / 100 = 1.5 → > 0.95 → red
        assert get_ltv_color(150) == "red"


# ===========================================================================
# assess_mortgage_risk_summary (backward compat)
# ===========================================================================

class TestAssessMortgageRiskSummary:

    def test_returns_string(self):
        result = assess_mortgage_risk_summary("High", 300_000, 250_000, 0.85)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_high_flood_risk_bad_ltv(self):
        result = assess_mortgage_risk_summary("High", 300_000, 290_000, 0.97)
        # Should be a high/critical risk label
        assert result  # non-empty

    def test_low_flood_risk_good_ltv(self):
        result = assess_mortgage_risk_summary("Low", 400_000, 200_000, 0.50)
        assert result


# ===========================================================================
# calculate_combined_risk (backward compat)
# ===========================================================================

class TestCalculateCombinedRisk:

    def test_returns_float(self):
        result = calculate_combined_risk("High", 0.85)
        assert isinstance(result, float)

    def test_high_risk_higher_than_low(self):
        high = calculate_combined_risk("High", 0.9)
        low = calculate_combined_risk("Low", 0.4)
        assert high > low

    def test_result_positive(self):
        result = calculate_combined_risk("Medium", 0.7)
        assert result >= 0


# ===========================================================================
# RiskAssessor backward-compat attributes
# ===========================================================================

class TestRiskAssessorBackwardCompat:

    def test_get_risk_color_on_class(self):
        from visual.utils.risk_assessors import RiskAssessor
        assert RiskAssessor.get_risk_color("High") == get_risk_color("High")

    def test_get_risk_icon_on_class(self):
        from visual.utils.risk_assessors import RiskAssessor
        assert RiskAssessor.get_risk_icon("Medium") == get_risk_icon("Medium")

    def test_get_ltv_color_on_class(self):
        from visual.utils.risk_assessors import RiskAssessor
        assert RiskAssessor.get_ltv_color(0.7) == get_ltv_color(0.7)
