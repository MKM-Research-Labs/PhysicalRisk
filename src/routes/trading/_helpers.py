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

"""Shared helpers for trading route sub-modules."""


def no_cache(response):
    """Prevent browser from caching any trading API response."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response

import logging

import database
from config import config

logger = logging.getLogger(__name__)


def _get_engines():
    """Lazily create and return trading engine instances."""
    from models.trading.market_state import MarketStateManager
    from models.trading.delta_engine import DeltaEngine
    from models.trading.pnl_engine import PnLEngine

    # Ensure the PRS reports dir exists (PRS trades still land there as files).
    config.get_reports_dir("prs").mkdir(parents=True, exist_ok=True)

    market_mgr = MarketStateManager()
    delta_eng = DeltaEngine(market_mgr)
    pnl_eng = PnLEngine()

    return market_mgr, delta_eng, pnl_eng


def _load_open_trades():
    """Load all PRS trades, merge with trade marks for status."""
    from models.trading.pnl_engine import PnLEngine

    catchment = config.catchment_id
    config.get_reports_dir("prs").mkdir(parents=True, exist_ok=True)

    pnl_eng = PnLEngine()
    marks = pnl_eng.load_trade_marks()

    trades = []
    for prs_id in database.iter_prs_trade_ids(catchment):
        if not prs_id.startswith('PRS-'):
            continue
        trade = database.get_prs_trade(catchment, prs_id)
        if trade is None:
            continue

        # Skip property PRS trades (served by /trading/client instead)
        if 'PropertySet' in trade.get('PhysicalSwap', {}):
            continue

        swap_id = trade.get('PhysicalSwap', {}).get(
            'Header', {}).get('SwapID', '')

        # Merge trade marks (status, inception mark, etc.)
        mark = marks.get(swap_id, {})
        trade['TradingMetadata'] = mark

        # Skip closed trades unless requested
        status = mark.get('trade_status', 'Open')
        trade.setdefault('PhysicalSwap', {}).setdefault(
            'Header', {})['TradeStatus'] = status

        trades.append(trade)

    return trades


def _load_gauge_locations() -> dict:
    """Load gauge locations from gaugehc.json (hazard_curves dict format)."""
    gauge_locations = {}
    gaugehc = database.get_gauge_hazard_curves(config.catchment_id)
    if gaugehc:
        curves = gaugehc.get('hazard_curves', {})
        for gid, gdata in curves.items():
            gauge_locations[gid] = {
                'lat': gdata.get('latitude', 0),
                'lon': gdata.get('longitude', 0),
                'name': gdata.get('gauge_name', gid),
            }
    return gauge_locations
