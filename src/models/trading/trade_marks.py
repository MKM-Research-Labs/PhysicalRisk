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

"""
Trade marks management for the trading desk.

Handles loading, saving, and updating supplementary mark data
(close-out, settlement) on top of PRS trade files.
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class TradeMarks:
    """Manages trade marks (supplementary data on top of PRS trade files)."""

    def __init__(self, trading_dir: Path):
        """
        Args:
            trading_dir: Path to data/input/<catchment>/blotter/
        """
        self.trading_dir = Path(trading_dir)
        self.marks_file = self.trading_dir / 'trade_marks.json'

    def load_trade_marks(self) -> Dict:
        """Load trade marks file."""
        if self.marks_file.exists():
            with open(self.marks_file) as f:
                return json.load(f)
        return {}

    def save_trade_marks(self, marks: Dict) -> None:
        """Save trade marks file."""
        with open(self.marks_file, 'w') as f:
            json.dump(marks, f, indent=2)

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
