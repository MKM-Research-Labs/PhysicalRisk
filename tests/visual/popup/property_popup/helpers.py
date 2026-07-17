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

"""Tests for _calculate_ltv_ratio, _extract_term_years, _calculate_monthly_payment."""

import pytest


# ---------------------------------------------------------------------------
# _calculate_ltv_ratio
# ---------------------------------------------------------------------------

class TestCalculateLtvRatio:

    def test_calculates_from_loan_and_value(self, builder):
        result = builder._calculate_ltv_ratio(300000, 400000, {})
        assert abs(result - 0.75) < 0.001

    def test_uses_stored_ratio_when_value_is_zero(self, builder):
        result = builder._calculate_ltv_ratio(300000, 0, {'LoanToValueRatio': 0.8})
        assert result == 0.8

    def test_uses_stored_ratio_when_value_is_none(self, builder):
        result = builder._calculate_ltv_ratio(300000, None, {'LoanToValueRatio': 0.65})
        assert result == 0.65

    def test_uses_stored_ratio_when_loan_not_numeric(self, builder):
        result = builder._calculate_ltv_ratio('N/A', 400000, {'LoanToValueRatio': 0.7})
        assert result == 0.7

    def test_returns_zero_when_all_missing(self, builder):
        result = builder._calculate_ltv_ratio(None, None, {})
        assert result == 0

    def test_full_ltv_when_loan_equals_value(self, builder):
        result = builder._calculate_ltv_ratio(500000, 500000, {})
        assert abs(result - 1.0) < 0.001


# ---------------------------------------------------------------------------
# _extract_term_years
# ---------------------------------------------------------------------------

class TestExtractTermYears:

    def test_finds_term_years_field(self, builder):
        assert builder._extract_term_years({'TermYears': 25}, {}) == 25

    def test_finds_term_field(self, builder):
        assert builder._extract_term_years({'Term': 30}, {}) == 30

    def test_finds_loan_term_field(self, builder):
        assert builder._extract_term_years({'LoanTerm': 20}, {}) == 20

    def test_original_term_in_months_converted(self, builder):
        result = builder._extract_term_years({'OriginalTerm': 300}, {})
        assert abs(result - 25.0) < 0.01

    def test_original_term_in_years_not_converted(self, builder):
        result = builder._extract_term_years({'OriginalTerm': 25}, {})
        assert result == 25

    def test_finds_term_years_in_nested_path(self, builder):
        result = builder._extract_term_years({}, {'term_years': 15})
        assert result == 15

    def test_returns_none_when_nothing_found(self, builder):
        assert builder._extract_term_years({}, {}) is None

    def test_priority_term_years_over_term(self, builder):
        result = builder._extract_term_years({'TermYears': 25, 'Term': 30}, {})
        assert result == 25


# ---------------------------------------------------------------------------
# _calculate_monthly_payment
# ---------------------------------------------------------------------------

class TestCalculateMonthlyPayment:

    def test_returns_stored_monthly_payment(self, builder):
        result = builder._calculate_monthly_payment(
            {'MonthlyPayment': 1500.0}, 300000, 0.04, 25
        )
        assert result == 1500.0

    def test_returns_stored_payment_field(self, builder):
        result = builder._calculate_monthly_payment(
            {'Payment': 1200.0}, 200000, 0.03, 20
        )
        assert result == 1200.0

    def test_returns_stored_regular_payment_field(self, builder):
        result = builder._calculate_monthly_payment(
            {'RegularPayment': 900.0}, 150000, 0.025, 15
        )
        assert result == 900.0

    def test_calculates_from_loan_rate_term(self, builder):
        result = builder._calculate_monthly_payment({}, 300000, 4.0, 25)
        # Standard amortisation: should be roughly £1,584/month
        assert result is not None
        assert 1500 < result < 1700

    def test_returns_none_when_loan_missing(self, builder):
        result = builder._calculate_monthly_payment({}, None, 0.04, 25)
        assert result is None

    def test_returns_none_when_rate_missing(self, builder):
        result = builder._calculate_monthly_payment({}, 300000, None, 25)
        assert result is None

    def test_returns_none_when_term_missing(self, builder):
        result = builder._calculate_monthly_payment({}, 300000, 0.04, None)
        assert result is None

    def test_zero_interest_rate_returns_none(self, builder):
        # monthly_rate = 0 → skips amortisation formula
        result = builder._calculate_monthly_payment({}, 300000, 0.0, 25)
        assert result is None
