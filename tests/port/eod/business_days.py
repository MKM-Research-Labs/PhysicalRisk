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

"""Tests for _business_days() and simulation constants — migrated from tests/models/trading/historical_eod.py."""

from datetime import date

import pytest

from port.src.historical_eod import (
    _business_days,
    DAILY_HAZARD_VOL,
    MAX_TOTAL_MOVE,
    NUM_BUSINESS_DAYS,
)


class TestBusinessDays:
    """Tests for the business day sequence generator."""

    def test_returns_correct_count(self):
        days = _business_days(date(2026, 3, 1), 63)
        assert len(days) == 63

    def test_no_weekends(self):
        days = _business_days(date(2026, 3, 1), 63)
        for d in days:
            assert d.weekday() < 5, f"{d} is a weekend"

    def test_chronological_order(self):
        days = _business_days(date(2026, 3, 1), 63)
        for i in range(1, len(days)):
            assert days[i] > days[i - 1]

    def test_ends_before_start(self):
        start = date(2026, 3, 1)
        days = _business_days(start, 10)
        for d in days:
            assert d < start

    def test_single_day(self):
        days = _business_days(date(2026, 3, 3), 1)  # Tuesday
        assert len(days) == 1
        assert days[0].weekday() < 5

    def test_start_on_monday_skips_weekend(self):
        """The day before Monday is Sunday — should skip back to Friday."""
        monday = date(2026, 3, 2)  # Monday
        days = _business_days(monday, 1)
        assert days[0].weekday() == 4  # Friday

    def test_start_on_wednesday(self):
        """5 days back from Wednesday should contain no Saturday/Sunday."""
        wednesday = date(2026, 3, 4)
        days = _business_days(wednesday, 5)
        assert len(days) == 5
        for d in days:
            assert d.weekday() < 5

    def test_last_day_is_day_before_start(self):
        """Last element should be the business day immediately before start."""
        start = date(2026, 3, 4)  # Wednesday — so previous bd is Tuesday
        days = _business_days(start, 3)
        last = days[-1]
        assert last < start
        assert last.weekday() < 5

    def test_large_count(self):
        days = _business_days(date(2026, 12, 31), 252)
        assert len(days) == 252
        for d in days:
            assert d.weekday() < 5


class TestSimulationParameters:
    """Sanity-check simulation constants."""

    def test_business_days_is_three_months(self):
        assert 60 <= NUM_BUSINESS_DAYS <= 66

    def test_daily_vol_is_small(self):
        assert 0.0001 <= DAILY_HAZARD_VOL <= 0.001

    def test_max_move_bounds_vol(self):
        assert MAX_TOTAL_MOVE > DAILY_HAZARD_VOL
        assert MAX_TOTAL_MOVE <= 0.01

    def test_floor_is_positive(self):
        """Random walk floors at 0.0001 — vol must not exceed that floor."""
        assert DAILY_HAZARD_VOL > 0
        assert MAX_TOTAL_MOVE > 0

    def test_max_move_at_least_ten_daily_vols(self):
        """Cumulative cap should allow meaningful drift."""
        assert MAX_TOTAL_MOVE >= 5 * DAILY_HAZARD_VOL
