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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Shared helpers for trading route sub-modules."""


def no_cache(response):
    """Prevent browser from caching any trading API response."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response

import json
import logging

from config import config

logger = logging.getLogger(__name__)


def _get_engines():
    """Lazily create and return trading engine instances."""
    from models.trading.market_state import MarketStateManager
    from models.trading.delta_engine import DeltaEngine
    from models.trading.pnl_engine import PnLEngine

    trading_dir = config.get_trading_dir()
    input_dir = config.get_input_dir()
    prs_dir = config.get_reports_dir("prs")
    prs_dir.mkdir(parents=True, exist_ok=True)

    market_mgr = MarketStateManager(trading_dir, input_dir)
    delta_eng = DeltaEngine(market_mgr)
    pnl_eng = PnLEngine(trading_dir, prs_dir)

    return market_mgr, delta_eng, pnl_eng


def _load_open_trades():
    """Load all PRS trades, merge with trade marks for status."""
    from models.trading.pnl_engine import PnLEngine

    prs_dir = config.get_reports_dir("prs")
    prs_dir.mkdir(parents=True, exist_ok=True)
    trading_dir = config.get_trading_dir()

    pnl_eng = PnLEngine(trading_dir, prs_dir)
    marks = pnl_eng.load_trade_marks()

    trades = []
    for f in sorted(prs_dir.glob("PRS-*.json")):
        with open(f) as fh:
            trade = json.load(fh)

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
    gaugehc_path = config.get_input_dir() / 'gaugehc.json'
    gauge_locations = {}
    if gaugehc_path.exists():
        with open(gaugehc_path) as f:
            gaugehc = json.load(f)
        curves = gaugehc.get('hazard_curves', {})
        for gid, gdata in curves.items():
            gauge_locations[gid] = {
                'lat': gdata.get('latitude', 0),
                'lon': gdata.get('longitude', 0),
                'name': gdata.get('gauge_name', gid),
            }
    return gauge_locations
