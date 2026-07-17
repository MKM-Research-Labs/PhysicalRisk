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

"""Tests for _business_days()."""

from datetime import date, timedelta
import pytest
from .conftest import _business_days


class TestBusinessDays:
    """Tests for _business_days()."""

    def test_returns_correct_count(self):
        today = date.today()
        result = _business_days(today, 5)
        assert len(result) == 5

    def test_returns_business_days_only(self):
        today = date.today()
        result = _business_days(today, 20)
        for d in result:
            assert d.weekday() < 5, f"{d} is a weekend"

    def test_returns_ascending_order(self):
        today = date.today()
        result = _business_days(today, 10)
        assert result == sorted(result)

    def test_single_day(self):
        today = date.today()
        result = _business_days(today, 1)
        assert len(result) == 1
        assert result[0].weekday() < 5

    def test_zero_days(self):
        today = date.today()
        result = _business_days(today, 0)
        assert result == []

    def test_skips_weekends(self):
        # Use a large enough window — 10 business days always spans ≥2 weekends
        today = date.today()
        result = _business_days(today, 10)
        all_days_in_range = set()
        d = result[0]
        while d <= result[-1]:
            all_days_in_range.add(d)
            d += timedelta(days=1)

        weekend_days_in_range = [d for d in all_days_in_range if d.weekday() >= 5]
        returned_set = set(result)
        for wd in weekend_days_in_range:
            assert wd not in returned_set, f"Weekend day {wd} found in result"

    def test_all_days_before_start(self):
        today = date.today()
        result = _business_days(today, 5)
        for d in result:
            assert d < today
