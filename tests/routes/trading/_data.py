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
Backward-compatible re-export shim.

After splitting _data.py into _data_part1.py and _data_part2.py, this file
re-exports all public names so existing ``from ._data import ...`` statements
continue to work without changes.
"""

from ._data_part1 import (  # noqa: F401
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    GAUGE_VAUXHALL, GAUGE_WATERLOO, GAUGE_BLACKFRIARS, GAUGE_LONDON,
    ALL_TEST_GAUGE_IDS,
    make_trade, make_gauge_entry,
    SAMPLE_GAUGEHC, SAMPLE_GAUGE_JSON,
)

from ._data_part2 import (  # noqa: F401
    CORE_TRADES, EXTENDED_TRADES, ALL_TRADES, TOTAL_TRADES,
    STORM_PORT_SEVERE, STORM_PORT_ALERT, SAMPLE_PORT_STRESS_STORMS,
    STORM_SEVERE, STORM_WARNING, SAMPLE_STRESS_STORMS,
)
