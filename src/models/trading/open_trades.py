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

"""The desk's open gauge-PRS trades, merged with their trade marks.

Shared by the trading routes and by anything outside Flask that needs the
book (the port pipeline's XVA stage), so neither reaches into the other.
Property PRS trades are left out: they are served by /trading/client.
"""

from typing import Dict, List

import database
from config import config


def load_open_trades() -> List[Dict]:
    """Every gauge PRS trade with its marks merged into ``TradingMetadata``."""
    from models.trading.pnl_engine import PnLEngine

    catchment = config.catchment_id
    config.get_reports_dir("prs").mkdir(parents=True, exist_ok=True)
    marks = PnLEngine().load_trade_marks()

    trades = []
    for prs_id in database.iter_prs_trade_ids(catchment):
        if not prs_id.startswith('PRS-'):
            continue
        trade = database.get_prs_trade(catchment, prs_id)
        if trade is None or 'PropertySet' in trade.get('PhysicalSwap', {}):
            continue
        swap_id = trade.get('PhysicalSwap', {}).get('Header', {}).get('SwapID', '')
        mark = marks.get(swap_id, {})
        trade['TradingMetadata'] = mark
        trade.setdefault('PhysicalSwap', {}).setdefault('Header', {})['TradeStatus'] = (
            mark.get('trade_status', 'Open'))
        trades.append(trade)
    return trades
