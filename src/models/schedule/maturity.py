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

"""
PRS maturity date convention.

Uses semi-annual roll dates (last Fridays of February and August).
Maturity dates fall on the last Friday of May (Feb roll) or November (Aug roll).
For tenor T on the current roll, maturity = last Friday of (roll_month + 3)
in year (roll_year + T).
"""

import calendar
from datetime import date, timedelta
from typing import Dict, List, Optional


def last_friday_of_month(year: int, month: int) -> date:
    """Return the last Friday of a given month."""
    # Find last day of month
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    # Walk back to Friday (weekday 4)
    offset = (d.weekday() - 4) % 7
    return d - timedelta(days=offset)


def current_roll_date(ref_date: Optional[date] = None) -> date:
    """
    Find the current roll date for a given reference date.

    Roll periods are determined by month:
    - Feb through Jul → Feb roll (last Friday of February)
    - Aug through Jan → Aug roll (last Friday of August)

    The roll becomes active at the start of the roll month,
    not on the specific Friday.
    """
    if ref_date is None:
        ref_date = date.today()

    month = ref_date.month
    year = ref_date.year

    if 2 <= month <= 7:
        # Feb roll period → May maturities
        return last_friday_of_month(year, 2)
    elif month >= 8:
        # Aug roll period → Nov maturities
        return last_friday_of_month(year, 8)
    else:
        # January → still on previous year's Aug roll
        return last_friday_of_month(year - 1, 8)


def compute_maturity_date(tenor_years: int, ref_date: Optional[date] = None) -> date:
    """
    Compute the maturity date for a given tenor.

    Uses the current roll date to determine the maturity month:
    - Feb roll → May maturity
    - Aug roll → November maturity

    Args:
        tenor_years: Tenor in whole years (1-5)
        ref_date: Reference date (defaults to today)

    Returns:
        Maturity date (last Friday of the maturity month)
    """
    roll = current_roll_date(ref_date)
    mat_month = roll.month + 3  # Feb(2)+3=May(5), Aug(8)+3=Nov(11)
    mat_year = roll.year + tenor_years

    if mat_month > 12:
        mat_month -= 12
        mat_year += 1

    return last_friday_of_month(mat_year, mat_month)


def maturity_table(max_tenor: int = 5,
                   ref_date: Optional[date] = None) -> List[Dict]:
    """
    Build a table of tenor → maturity date mappings.

    Returns:
        List of dicts with keys: tenor, maturity_date, maturity_str, actual_years
    """
    if ref_date is None:
        ref_date = date.today()

    table = []
    for t in range(1, max_tenor + 1):
        mat = compute_maturity_date(t, ref_date)
        actual = (mat - ref_date).days / 365.25
        table.append({
            'tenor': t,
            'maturity_date': mat,
            'maturity_str': mat.strftime('%d %b %Y'),
            'actual_years': round(actual, 2),
        })

    return table


def tenor_from_maturity(maturity_date: date,
                        ref_date: Optional[date] = None,
                        max_tenor: int = 5) -> int:
    """
    Reverse lookup: find the tenor label for a given maturity date.

    Returns the tenor (1-5) whose maturity matches, or the closest match.
    """
    table = maturity_table(max_tenor, ref_date)
    for entry in table:
        if entry['maturity_date'] == maturity_date:
            return entry['tenor']

    # Closest match by date distance
    best = min(table, key=lambda e: abs((e['maturity_date'] - maturity_date).days))
    return best['tenor']
