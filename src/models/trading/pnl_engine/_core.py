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
P&L engine for the trading desk.

Computes daily and running P&L and EOD snapshots. Daily P&L decomposition:

- New trade P&L = (fair_spread - trade_spread) / 10000 * annuity * notional * dir
- Market move P&L = (today_fair - yesterday_fair) / 10000 * annuity * notional * dir
- Daily P&L = new_trade_pnl + market_move_pnl
- Running P&L = sum of all daily P&L since inception
"""

from typing import Dict, List, Optional

import database
from config import config

from ..trade_marks import TradeMarks
from ._pnl import _PnLComputeMixin


class PnLEngine(_PnLComputeMixin, TradeMarks):
    """Computes and manages P&L for the trading desk."""

    def __init__(self, catchment: Optional[str] = None):
        """
        Args:
            catchment: Catchment to operate on (defaults to ``database.active_catchment()``).
        """
        super().__init__(catchment)

    def get_eod_history(self) -> List[Dict]:
        """Get list of all EOD snapshots (summaries only), newest first."""
        # EOD report PDFs stay file-based (out of scope); resolve their dir from config.
        eod_dir = config.get_eod_dir()
        history = []
        for snapshot in sorted(database.iter_eod_snapshots(self.catchment),
                               key=lambda s: s.get('date', ''), reverse=True):
            summary = snapshot.get('portfolio_summary', {})
            eod_date = snapshot.get('date', '')
            # Check if a PDF report exists for this EOD
            pdf_name = f"EOD-{eod_date.replace('-', '')}.pdf"
            has_pdf = (eod_dir / pdf_name).exists()
            history.append({
                'eod_id': snapshot.get('eod_id', ''),
                'date': eod_date,
                'num_open_trades': summary.get('num_open_trades', 0),
                'total_notional': summary.get('total_notional', 0),
                'total_daily_pnl': summary.get('total_daily_pnl', 0),
                'total_running_pnl': summary.get('total_running_pnl', 0),
                'has_pdf': has_pdf,
            })
        return history

    def get_eod_snapshot(self, eod_date: str) -> Optional[Dict]:
        """Load a specific EOD snapshot by date through the database seam."""
        return database.get_eod_snapshot(self.catchment, eod_date)

    def get_pnl_series(self) -> List[Dict]:
        """
        Get time series of daily P&L for charting.

        Returns:
            List of {date, daily_pnl, running_pnl} dicts, chronological.
        """
        series = []
        for snapshot in sorted(database.iter_eod_snapshots(self.catchment),
                               key=lambda s: s.get('date', '')):
            summary = snapshot.get('portfolio_summary', {})
            series.append({
                'date': snapshot.get('date', ''),
                'daily_pnl': summary.get('total_daily_pnl', 0),
                'running_pnl': summary.get('total_running_pnl', 0),
                'from_trades': summary.get('daily_pnl_from_trades', 0),
                'from_market': summary.get('daily_pnl_from_market', 0),
                'num_trades': summary.get('num_open_trades', 0),
            })
        return series
