# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for config.loan — discount curve, credit/hazard spreads, coupon build-up."""

import pytest

from config.loan import (
    DISCOUNT_CURVE,
    CREDIT_RATING_SPREADS,
    CREDIT_RATINGS,
    COMMERCIAL_MAX_TERM_YEARS,
    discount_rate,
    credit_spread_for_rating,
    flood_hazard_spread,
    wind_hazard_spread,
    build_coupon,
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


class TestHazardSpreads:

    def test_flood_monotonic_and_case_insensitive(self):
        assert (flood_hazard_spread("Very low") < flood_hazard_spread("Medium")
                < flood_hazard_spread("Very high"))
        assert flood_hazard_spread("VERY HIGH") == flood_hazard_spread("very high")

    def test_wind_monotonic(self):
        assert (wind_hazard_spread("Very low") < wind_hazard_spread("Medium")
                < wind_hazard_spread("Very high"))

    def test_unknown_category_falls_back_to_medium(self):
        assert flood_hazard_spread("bogus") == flood_hazard_spread("Medium")


class TestBuildCoupon:

    def test_bbb_medium_medium_lands_near_seven_percent(self):
        c = build_coupon(term_years=3, credit_rating="BBB",
                         flood_category="Medium", wind_category="Medium")
        assert c["rate"] == pytest.approx(0.070, abs=1e-9)

    def test_components_sum_to_rate(self):
        c = build_coupon(term_years=5, credit_rating="BB",
                         flood_category="High", wind_category="Low")
        assert c["rate"] == pytest.approx(
            c["risk_free"] + c["credit_spread"] + c["flood_spread"] + c["wind_spread"])
        assert c["hazard_spread"] == pytest.approx(c["flood_spread"] + c["wind_spread"])

    def test_commercial_cap_constant(self):
        assert COMMERCIAL_MAX_TERM_YEARS == 7
