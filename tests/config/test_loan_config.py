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

"""Tests for config.loan — discount curve, credit/hazard spreads, coupon build-up."""

import pytest

from config.loan import (
    DISCOUNT_CURVE,
    CREDIT_RATING_SPREADS,
    CREDIT_RATINGS,
    COMMERCIAL_MAX_TERM_YEARS,
    FLOOD_CATEGORY_ANNUAL_HAZARD,
    PRS_FLOOD_RECOVERY,
    discount_rate,
    credit_spread_for_rating,
    flood_annual_hazard,
    wind_hazard_spread,
)


class TestDiscountCurve:

    def test_curve_centres_on_about_4_5_percent(self):
        # The 3y reference point is exactly 4.5%.
        assert DISCOUNT_CURVE[3] == pytest.approx(0.045)
        # Whole curve sits in a tight band around 4.5%.
        assert all(0.040 <= r <= 0.050 for r in DISCOUNT_CURVE.values())

    def test_discount_rate_interpolates(self):
        # Halfway between 1y (4.20%) and 2y (4.40%) -> 4.30%.
        assert discount_rate(1.5) == pytest.approx(0.043)

    def test_discount_rate_clamps_outside_range(self):
        assert discount_rate(0.25) == DISCOUNT_CURVE[min(DISCOUNT_CURVE)]
        assert discount_rate(100) == DISCOUNT_CURVE[max(DISCOUNT_CURVE)]


class TestCreditSpreads:

    def test_monotonic_worsening(self):
        spreads = [CREDIT_RATING_SPREADS[r] for r in CREDIT_RATINGS]
        assert spreads == sorted(spreads)  # AAA cheapest ... CCC dearest

    def test_unknown_rating_falls_back_to_default(self):
        assert credit_spread_for_rating("ZZZ") == CREDIT_RATING_SPREADS["BBB"]
        assert credit_spread_for_rating(None) == CREDIT_RATING_SPREADS["BBB"]

    def test_case_insensitive(self):
        assert credit_spread_for_rating("bbb") == CREDIT_RATING_SPREADS["BBB"]


class TestFloodAnnualHazard:
    """Flood category → annual flood probability (the PRS pricer's input)."""

    def test_monotonic_with_severity(self):
        assert (flood_annual_hazard("Very low") < flood_annual_hazard("Medium")
                < flood_annual_hazard("Very high"))

    def test_case_and_space_insensitive(self):
        assert flood_annual_hazard("VERY HIGH") == flood_annual_hazard("very high")
        assert flood_annual_hazard("  Medium  ") == flood_annual_hazard("medium")

    def test_unknown_category_falls_back_to_medium(self):
        assert flood_annual_hazard("bogus") == flood_annual_hazard("Medium")

    def test_ea_zone_aligned_values(self):
        # EA flood-zone midpoints: Zone 1 ≈ 0.001 … Zone 3b ≈ 0.050.
        assert FLOOD_CATEGORY_ANNUAL_HAZARD["very low"] == pytest.approx(0.001)
        assert FLOOD_CATEGORY_ANNUAL_HAZARD["very high"] == pytest.approx(0.050)
        probs = [FLOOD_CATEGORY_ANNUAL_HAZARD[c]
                 for c in ("very low", "low", "medium", "high", "very high")]
        assert probs == sorted(probs)

    def test_recovery_is_full_loss(self):
        # 0% recovery == full loss given a flood trigger.
        assert PRS_FLOOD_RECOVERY == pytest.approx(0.0)


class TestWindHazardSpread:
    """Wind keeps the static lookup (no PRS wind pricer yet)."""

    def test_monotonic(self):
        assert (wind_hazard_spread("Very low") < wind_hazard_spread("Medium")
                < wind_hazard_spread("Very high"))

    def test_case_insensitive(self):
        assert wind_hazard_spread("VERY HIGH") == wind_hazard_spread("very high")

    def test_unknown_category_falls_back_to_medium(self):
        assert wind_hazard_spread("bogus") == wind_hazard_spread("Medium")


class TestTermCaps:

    def test_commercial_cap_constant(self):
        assert COMMERCIAL_MAX_TERM_YEARS == 7
