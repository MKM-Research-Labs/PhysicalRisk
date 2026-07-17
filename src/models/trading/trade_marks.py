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
Trade marks management for the trading desk.

Handles loading, saving, and updating supplementary mark data
(close-out, settlement) on top of PRS trade files.
"""

import logging
from datetime import date
from typing import Dict, Optional

import database

logger = logging.getLogger(__name__)


class TradeMarks:
    """Manages trade marks (supplementary data on top of PRS trade files)."""

    def __init__(self, catchment: Optional[str] = None):
        """
        Args:
            catchment: Catchment to operate on (defaults to ``database.active_catchment()``).
        """
        self.catchment = catchment or database.active_catchment()

    def load_trade_marks(self) -> Dict:
        """Load trade marks through the database seam (missing → {})."""
        return database.get_trade_marks(self.catchment)

    def save_trade_marks(self, marks: Dict) -> None:
        """Persist trade marks through the database seam."""
        database.save_trade_marks(self.catchment, marks)

    def get_trade_mark(self, swap_id: str) -> Dict:
        """Get mark data for a specific trade."""
        marks = self.load_trade_marks()
        return marks.get(swap_id, {})

    def update_trade_mark(self, swap_id: str, mark_data: Dict) -> None:
        """Update mark for a specific trade."""
        marks = self.load_trade_marks()
        if swap_id not in marks:
            marks[swap_id] = {}
        marks[swap_id].update(mark_data)
        self.save_trade_marks(marks)

    def close_trade(self, swap_id: str, close_spread_bps: float,
                     final_pnl: float = 0.0,
                     original_notional: float = 0.0) -> Dict:
        """
        Close out a trade at the given spread.

        Zeroes notional but preserves final P&L and settlement data.

        Args:
            swap_id: Trade identifier
            close_spread_bps: Spread at which the trade is closed
            final_pnl: Final running P&L to preserve
            original_notional: Original notional before zeroing

        Returns:
            Updated mark data for the trade
        """
        marks = self.load_trade_marks()
        if swap_id not in marks:
            marks[swap_id] = {}

        marks[swap_id]['trade_status'] = 'Closed'
        marks[swap_id]['close_date'] = date.today().isoformat()
        marks[swap_id]['close_spread_bps'] = close_spread_bps
        marks[swap_id]['final_pnl'] = round(final_pnl, 2)
        marks[swap_id]['settlement_amount'] = round(abs(final_pnl), 2)
        marks[swap_id]['original_notional'] = original_notional
        self.save_trade_marks(marks)

        logger.info("Trade %s closed at %.1f bps, P&L: %.2f",
                     swap_id, close_spread_bps, final_pnl)
        return marks[swap_id]
