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
