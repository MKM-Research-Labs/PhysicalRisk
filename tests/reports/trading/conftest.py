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

"""Shared test data for reports/trading EOD page tests."""


# ===========================================================================
# Sample data
# ===========================================================================

BASE_SNAPSHOT = {
    "eod_id": "EOD-2026-03-08",
    "date": "2026-03-08",
    "portfolio_summary": {
        "num_open_trades": 3,
        "total_notional": 25_000_000,
        "total_daily_pnl": 12_500,
        "daily_pnl_from_trades": 5_000,
        "daily_pnl_from_market": 7_500,
        "total_running_pnl": 45_000,
    },
    "positions": [
        {
            "swap_id": "PRS-001",
            "gauge_id": "GAUGE-001",
            "trigger": "warning",
            "notional": 10_000_000,
            "tenor": 3,
            "trade_spread_bps": 150.0,
            "fair_spread_bps": 145.0,
            "gauge_fs01": 2500.0,
            "daily_pnl": 5_000.0,
            "running_pnl": 20_000.0,
            "new_trade_pnl": 5_000.0,
            "market_pnl": 0.0,
        },
        {
            "swap_id": "PRS-002",
            "gauge_id": "GAUGE-001",
            "trigger": "severe",
            "notional": 8_000_000,
            "tenor": 5,
            "trade_spread_bps": 200.0,
            "fair_spread_bps": 198.0,
            "gauge_fs01": -1500.0,
            "daily_pnl": 2_500.0,
            "running_pnl": 15_000.0,
            "new_trade_pnl": 0.0,
            "market_pnl": 2_500.0,
        },
        {
            "swap_id": "PRS-003",
            "gauge_id": "GAUGE-002",
            "trigger": "alert",
            "notional": 7_000_000,
            "tenor": 2,
            "trade_spread_bps": 100.0,
            "fair_spread_bps": 102.0,
            "gauge_fs01": 1000.0,
            "daily_pnl": 5_000.0,
            "running_pnl": 10_000.0,
            "new_trade_pnl": 0.0,
            "market_pnl": 5_000.0,
        },
    ],
}

EMPTY_SNAPSHOT = {
    "eod_id": "EOD-2026-03-08",
    "date": "2026-03-08",
    "portfolio_summary": {},
    "positions": [],
}

PNL_SERIES = [
    {"date": "2026-03-07", "daily_pnl": 10_000, "running_pnl": 32_500,
     "from_trades": 5_000, "from_market": 5_000},
    {"date": "2026-03-08", "daily_pnl": 12_500, "running_pnl": 45_000,
     "from_trades": 5_000, "from_market": 7_500},
]
