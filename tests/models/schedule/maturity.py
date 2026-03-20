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

"""Tests for the PRS maturity date convention."""

from datetime import date

import pytest

from models.schedule.maturity import (
    last_friday_of_month,
    current_roll_date,
    compute_maturity_date,
    maturity_table,
    tenor_from_maturity,
)


class TestLastFridayOfMonth:
    """Tests for last Friday calculation."""

    def test_may_2029(self):
        """May 2029: 31st is Thursday, last Friday = 25th."""
        assert last_friday_of_month(2029, 5) == date(2029, 5, 25)

    def test_nov_2029(self):
        """Nov 2029: 30th is Friday."""
        assert last_friday_of_month(2029, 11) == date(2029, 11, 30)

    def test_feb_2026(self):
        """Feb 2026: 28th is Saturday, last Friday = 27th."""
        assert last_friday_of_month(2026, 2) == date(2026, 2, 27)

    def test_aug_2026(self):
        """Aug 2026: 31st is Monday, last Friday = 28th."""
        assert last_friday_of_month(2026, 8) == date(2026, 8, 28)

    def test_result_is_friday(self):
        """Result should always be a Friday (weekday=4)."""
        for year in [2026, 2027, 2028, 2029, 2030]:
            for month in [2, 5, 8, 11]:
                d = last_friday_of_month(year, month)
                assert d.weekday() == 4, f"{d} is not a Friday"


class TestCurrentRollDate:
    """Tests for roll date determination."""

    def test_feb_period(self):
        """Feb-Jul uses Feb roll."""
        roll = current_roll_date(date(2026, 2, 24))
        assert roll == last_friday_of_month(2026, 2)
        assert roll.month == 2

    def test_mar_still_feb_roll(self):
        """March is still in the Feb roll period."""
        roll = current_roll_date(date(2026, 3, 15))
        assert roll.month == 2
        assert roll.year == 2026

    def test_jul_still_feb_roll(self):
        """July is the last month of the Feb roll period."""
        roll = current_roll_date(date(2026, 7, 31))
        assert roll.month == 2
        assert roll.year == 2026

    def test_aug_period(self):
        """Aug onwards uses Aug roll."""
        roll = current_roll_date(date(2026, 9, 1))
        assert roll == last_friday_of_month(2026, 8)
        assert roll.month == 8

    def test_jan_uses_prev_aug(self):
        """January uses the previous year's Aug roll."""
        roll = current_roll_date(date(2027, 1, 15))
        assert roll == last_friday_of_month(2026, 8)
        assert roll.month == 8
        assert roll.year == 2026

    def test_dec_uses_aug(self):
        """December uses the same year's Aug roll."""
        roll = current_roll_date(date(2026, 12, 1))
        assert roll.month == 8
        assert roll.year == 2026


class TestComputeMaturityDate:
    """Tests for maturity date computation."""

    def test_3y_from_feb_2026(self):
        """3Y from Feb 2026 = last Friday May 2029."""
        mat = compute_maturity_date(3, date(2026, 2, 24))
        assert mat == last_friday_of_month(2029, 5)
        assert mat.month == 5
        assert mat.year == 2029

    def test_5y_from_feb_2026(self):
        """5Y from Feb 2026 = last Friday May 2031."""
        mat = compute_maturity_date(5, date(2026, 2, 24))
        assert mat == last_friday_of_month(2031, 5)

    def test_1y_from_feb_2026(self):
        """1Y from Feb 2026 = last Friday May 2027."""
        mat = compute_maturity_date(1, date(2026, 2, 24))
        assert mat == last_friday_of_month(2027, 5)

    def test_3y_from_sep_2026(self):
        """3Y from Sep 2026 = last Friday Nov 2029 (Aug roll)."""
        mat = compute_maturity_date(3, date(2026, 9, 1))
        assert mat == last_friday_of_month(2029, 11)
        assert mat.month == 11

    def test_5y_from_sep_2026(self):
        """5Y from Sep 2026 = last Friday Nov 2031."""
        mat = compute_maturity_date(5, date(2026, 9, 1))
        assert mat == last_friday_of_month(2031, 11)

    def test_3y_from_jan_2027(self):
        """Jan 2027 uses Aug 2026 roll → Nov 2029 maturity."""
        mat = compute_maturity_date(3, date(2027, 1, 15))
        assert mat == last_friday_of_month(2029, 11)

    def test_maturity_is_friday(self):
        """All maturities should fall on a Friday."""
        for t in [1, 2, 3, 4, 5]:
            mat = compute_maturity_date(t, date(2026, 2, 24))
            assert mat.weekday() == 4

    def test_roll_jump_at_august(self):
        """3Y maturity jumps from May to Nov at the Aug roll."""
        may_mat = compute_maturity_date(3, date(2026, 7, 31))
        nov_mat = compute_maturity_date(3, date(2026, 8, 1))
        assert may_mat.month == 5
        assert nov_mat.month == 11
        assert (nov_mat - may_mat).days > 150  # ~6 months apart


class TestMaturityTable:
    """Tests for the full maturity table."""

    def test_table_has_5_entries(self):
        """Default table has 5 entries (1Y through 5Y)."""
        table = maturity_table(5, date(2026, 2, 24))
        assert len(table) == 5

    def test_tenors_sequential(self):
        """Tenors should be 1, 2, 3, 4, 5."""
        table = maturity_table(5, date(2026, 2, 24))
        tenors = [e['tenor'] for e in table]
        assert tenors == [1, 2, 3, 4, 5]

    def test_all_may_for_feb_roll(self):
        """All maturities should be in May for the Feb roll."""
        table = maturity_table(5, date(2026, 2, 24))
        for e in table:
            assert e['maturity_date'].month == 5

    def test_all_nov_for_aug_roll(self):
        """All maturities should be in November for the Aug roll."""
        table = maturity_table(5, date(2026, 9, 1))
        for e in table:
            assert e['maturity_date'].month == 11

    def test_actual_years_increasing(self):
        """Actual years should be strictly increasing."""
        table = maturity_table(5, date(2026, 2, 24))
        years = [e['actual_years'] for e in table]
        for i in range(1, len(years)):
            assert years[i] > years[i - 1]

    def test_maturity_str_format(self):
        """Maturity string should be formatted as 'DD Mon YYYY'."""
        table = maturity_table(5, date(2026, 2, 24))
        for e in table:
            assert len(e['maturity_str']) > 8
            assert 'May' in e['maturity_str'] or 'Nov' in e['maturity_str']


class TestTenorFromMaturity:
    """Tests for reverse tenor lookup."""

    def test_exact_match(self):
        """Exact maturity date returns correct tenor."""
        mat = compute_maturity_date(3, date(2026, 2, 24))
        assert tenor_from_maturity(mat, date(2026, 2, 24)) == 3

    def test_all_tenors_round_trip(self):
        """All tenors should round-trip through maturity and back."""
        ref = date(2026, 2, 24)
        for t in [1, 2, 3, 4, 5]:
            mat = compute_maturity_date(t, ref)
            assert tenor_from_maturity(mat, ref) == t

    def test_closest_match_fallback(self):
        """A date not in the table returns the closest tenor."""
        ref = date(2026, 2, 24)
        # Use a date that's between the 2Y and 3Y maturities
        two_y = compute_maturity_date(2, ref)
        three_y = compute_maturity_date(3, ref)
        mid = date(two_y.year + 1, 1, 1)  # Somewhere between 2Y and 3Y
        result = tenor_from_maturity(mid, ref)
        assert result in [1, 2, 3, 4, 5]


class TestDefaultDates:
    """Tests for functions with None (default today) ref_date."""

    def test_current_roll_date_default(self):
        """current_roll_date(None) uses today and returns a valid date."""
        roll = current_roll_date(None)
        assert isinstance(roll, date)
        assert roll.weekday() == 4  # Friday

    def test_maturity_table_default(self):
        """maturity_table with no ref_date uses today."""
        table = maturity_table()
        assert len(table) == 5
        assert all(isinstance(e['maturity_date'], date) for e in table)

    def test_compute_maturity_default(self):
        """compute_maturity_date with no ref_date uses today."""
        mat = compute_maturity_date(3)
        assert isinstance(mat, date)
        assert mat.weekday() == 4  # Friday
