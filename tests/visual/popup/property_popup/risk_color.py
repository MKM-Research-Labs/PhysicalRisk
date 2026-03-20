# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for _get_mortgage_risk_summary and _get_overall_risk_color."""

import pytest


# ---------------------------------------------------------------------------
# _get_mortgage_risk_summary
# ---------------------------------------------------------------------------

class TestGetMortgageRiskSummary:

    def test_high_flood_risk(self, builder):
        result = builder._get_mortgage_risk_summary('High', 300000, 300000, 0.5)
        assert 'High Risk' in result
        assert 'flood' in result.lower()

    def test_very_high_flood_risk(self, builder):
        result = builder._get_mortgage_risk_summary('Very High', 300000, 300000, 0.5)
        assert 'High Risk' in result

    def test_critical_risk_large_negative_value(self, builder):
        # mortgage_value negative and >10% of loan_amount
        result = builder._get_mortgage_risk_summary('Low', -35000, 300000, 0.5)
        assert 'Critical Risk' in result

    def test_high_risk_moderate_negative_value(self, builder):
        # >5% but <=10%
        result = builder._get_mortgage_risk_summary('Low', -18000, 300000, 0.5)
        assert 'High Risk' in result
        assert 'negative' in result.lower()

    def test_moderate_risk_small_negative_value(self, builder):
        # >2% but <=5%
        result = builder._get_mortgage_risk_summary('Low', -9000, 300000, 0.5)
        assert 'Moderate Risk' in result

    def test_high_ltv_with_medium_risk(self, builder):
        result = builder._get_mortgage_risk_summary('Medium', 300000, 300000, 0.85)
        assert 'High Risk' in result
        assert 'LTV' in result

    def test_elevated_ltv_with_medium_risk(self, builder):
        result = builder._get_mortgage_risk_summary('Medium', 300000, 300000, 0.75)
        assert 'Moderate Risk' in result
        assert 'LTV' in result

    def test_medium_flood_risk_low_ltv(self, builder):
        result = builder._get_mortgage_risk_summary('Medium', 300000, 300000, 0.5)
        assert 'Moderate Risk' in result
        assert 'flood' in result.lower()

    def test_low_flood_risk(self, builder):
        result = builder._get_mortgage_risk_summary('Low', 300000, 300000, 0.5)
        assert 'Low Risk' in result

    def test_minimal_risk_unknown_level(self, builder):
        result = builder._get_mortgage_risk_summary('Unknown', 300000, 300000, 0.5)
        assert 'Minimal Risk' in result


# ---------------------------------------------------------------------------
# _get_overall_risk_color
# ---------------------------------------------------------------------------

class TestGetOverallRiskColor:

    def test_high_flood_risk_is_red(self, builder):
        assert builder._get_overall_risk_color('High', 300000, 300000, 0.5) == 'red'

    def test_very_high_flood_risk_is_red(self, builder):
        assert builder._get_overall_risk_color('Very High', 300000, 300000, 0.5) == 'red'

    def test_large_negative_value_is_red(self, builder):
        # abs(mortgage_value) > loan_amount * 0.05
        assert builder._get_overall_risk_color('Low', -20000, 300000, 0.5) == 'red'

    def test_medium_flood_risk_is_orange(self, builder):
        assert builder._get_overall_risk_color('Medium', 300000, 300000, 0.5) == 'orange'

    def test_small_negative_value_is_orange(self, builder):
        # abs(mortgage_value) > loan_amount * 0.02 but not > 0.05
        assert builder._get_overall_risk_color('Low', -7500, 300000, 0.5) == 'orange'

    def test_low_flood_risk_is_goldenrod(self, builder):
        assert builder._get_overall_risk_color('Low', 300000, 300000, 0.5) == 'goldenrod'

    def test_minimal_risk_is_green(self, builder):
        assert builder._get_overall_risk_color('Unknown', 300000, 300000, 0.3) == 'green'

    def test_very_low_flood_risk_is_green(self, builder):
        assert builder._get_overall_risk_color('Very Low', 300000, 300000, 0.3) == 'green'
