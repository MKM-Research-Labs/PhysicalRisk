# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for the loan-pricing coupon helpers — _truthy numeric/string
branches and the _peril_leg non-numeric / off / negative paths."""

from routes._loan_pricing._coupon import _truthy, _peril_leg


class TestTruthy:
    def test_numeric_nonzero_true_and_zero_false(self):
        assert _truthy(1) is True       # line 43 (int != 0)
        assert _truthy(0.0) is False    # line 43
        assert _truthy(2.5) is True

    def test_string_tokens(self):
        assert _truthy("on") is True    # line 45
        assert _truthy("YES") is True
        assert _truthy("nope") is False

    def test_other_types_false(self):
        assert _truthy(None) is False
        assert _truthy(object()) is False


class TestPerilLeg:
    def test_off_or_missing_is_zero(self):
        assert _peril_leg(100.0, False) == 0.0
        assert _peril_leg(None, True) == 0.0

    def test_non_numeric_spread_returns_zero(self):
        assert _peril_leg("not-a-number", True) == 0.0  # lines 55-56

    def test_negative_spread_returns_zero(self):
        assert _peril_leg(-50.0, True) == 0.0

    def test_positive_spread_to_decimal(self):
        assert _peril_leg(100.0, True) == 0.01
