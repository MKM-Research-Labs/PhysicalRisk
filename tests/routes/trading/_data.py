# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
