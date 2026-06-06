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

"""Historical EOD series generator (curve random walk + revaluation)."""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

from config.port import DAILY_HAZARD_VOL, MAX_TOTAL_MOVE, NUM_BUSINESS_DAYS

from ._business_days import _business_days
from ._history import (
    generate_hazard_curve_history_file,
    generate_trade_pnl_history_file,
)


def generate_historical_eod_series(
    trades: List[Dict],
    trading_dir,
    input_dir,
    prs_dir,
    seed: Optional[int] = 42,
) -> int:
    """
    Generate a historical EOD series with curve evolution.

    Args:
        trades: List of trade dicts (from book generator)
        trading_dir: Path to data/input/<catchment>/blotter/
        input_dir: Path to data/input/<catchment>/
        prs_dir: Path to data/input/<catchment>/prs/ (PRS trade files)
        seed: Random seed for reproducibility

    Returns:
        Number of EOD snapshots generated
    """
    from models.trading.market_state import MarketStateManager
    from models.trading.delta_engine import DeltaEngine, compute_prs_spread, compute_risky_annuity
    from models.trading.pnl_engine import PnLEngine

    trading_dir = Path(trading_dir)
    input_dir = Path(input_dir)
    prs_dir = Path(prs_dir)

    rng = np.random.RandomState(seed)

    # Initialize engines
    market_mgr = MarketStateManager(trading_dir, input_dir)
    delta_eng = DeltaEngine(market_mgr)
    pnl_eng = PnLEngine(trading_dir, prs_dir)

    # Load fresh market state (base curves)
    state = market_mgr.load()

    # Store original base term structures for clamping
    base_ts = {}
    for gauge_id, triggers in state.get('hazard_term_structure', {}).items():
        base_ts[gauge_id] = {}
        for trigger, tenors in triggers.items():
            base_ts[gauge_id][trigger] = {k: v for k, v in tenors.items()}

    # Generate business days ending yesterday
    today = date.today()
    sim_days = _business_days(today, NUM_BUSINESS_DAYS)

    # Clean existing EOD snapshots
    eod_dir = pnl_eng.eod_dir
    for f in eod_dir.glob('EOD-*.json'):
        f.unlink()

    # Sort trades by swap_id for deterministic ordering
    sorted_trades = sorted(trades, key=lambda t: t.get('PhysicalSwap', {}).get('Header', {}).get('SwapID', ''))

    num_snapshots = 0
    open_trade_set = []  # Trades added so far

    for day_idx, sim_date in enumerate(sim_days):
        date_str = sim_date.isoformat()

        # --- 1. Add one trade from the book (if any remain) ---
        if day_idx < len(sorted_trades):
            trade = sorted_trades[day_idx]
            # Backdate the trade to this simulation date
            header = trade.get('PhysicalSwap', {}).get('Header', {})
            header['ValuationDate'] = date_str
            header['ProtectionStart'] = date_str
            open_trade_set.append(trade)

        if not open_trade_set:
            continue

        # --- 2. Random walk on hazard term structures ---
        ts = state.get('hazard_term_structure', {})
        for gauge_id in ts:
            for trigger in ts[gauge_id]:
                for tenor_str in ts[gauge_id][trigger]:
                    current = ts[gauge_id][trigger][tenor_str]
                    shock = rng.normal(0, DAILY_HAZARD_VOL)
                    new_rate = current + shock

                    # Clamp total move from base
                    base_rate = base_ts.get(gauge_id, {}).get(trigger, {}).get(tenor_str, current)
                    move = new_rate - base_rate
                    if abs(move) > MAX_TOTAL_MOVE:
                        new_rate = base_rate + MAX_TOTAL_MOVE * np.sign(move)

                    # Floor at 0.0001 (0.1bp)
                    ts[gauge_id][trigger][tenor_str] = max(0.0001, round(new_rate, 6))

        state['hazard_term_structure'] = ts
        state['last_updated'] = f"{date_str}T17:00:00"

        # Save market state for this day
        with open(market_mgr.state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # --- 3. Revalue all open trades ---
        enriched = []
        for t in open_trade_set:
            try:
                e = delta_eng.enrich_trade(t, state)
                # Override trade_date to sim_date for new-trade P&L detection
                swap_id = t.get('PhysicalSwap', {}).get('Header', {}).get('SwapID', '')
                if day_idx < len(sorted_trades) and t is sorted_trades[day_idx]:
                    e['trade_date'] = date_str
                else:
                    e['trade_date'] = ''  # Not new today
                enriched.append(e)
            except Exception as exc:
                logger.debug("Skip trade enrichment on %s: %s", date_str, exc)

        if not enriched:
            continue

        # --- 4. Generate EOD snapshot ---
        snapshot = pnl_eng.generate_eod_snapshot(enriched, state, date_str)
        num_snapshots += 1

        if day_idx % 10 == 0 or day_idx == len(sim_days) - 1:
            pnl = snapshot.get('portfolio_summary', {}).get('total_daily_pnl', 0)
            n_trades = snapshot.get('portfolio_summary', {}).get('num_open_trades', 0)
            logger.info("EOD %s: %d trades, daily P&L: %.0f",
                        date_str, n_trades, pnl)

    # Write hazard curve history from all EOD snapshots
    history_path = trading_dir / 'hazard_curve_history.json'
    generate_hazard_curve_history_file(eod_dir, history_path)

    # Write per-trade P&L history from all EOD snapshots
    trade_history_path = trading_dir / 'trade_pnl_history.json'
    generate_trade_pnl_history_file(eod_dir, trade_history_path)

    return num_snapshots
