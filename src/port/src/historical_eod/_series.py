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

"""Historical EOD series generator (curve random walk + revaluation)."""

import logging
from datetime import date
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
    catchment: Optional[str] = None,
    seed: Optional[int] = 42,
) -> int:
    """
    Generate a historical EOD series with curve evolution.

    Args:
        trades: List of trade dicts (from book generator)
        catchment: Catchment to operate on (defaults to ``database.active_catchment()``).
        seed: Random seed for reproducibility

    Returns:
        Number of EOD snapshots generated
    """
    import database
    from models.trading.market_state import MarketStateManager
    from models.trading.delta_engine import DeltaEngine
    from models.trading.pnl_engine import PnLEngine

    catchment = catchment or database.active_catchment()

    rng = np.random.RandomState(seed)

    # Initialize engines (all persist through the database seam)
    market_mgr = MarketStateManager(catchment)
    delta_eng = DeltaEngine(market_mgr)
    pnl_eng = PnLEngine(catchment)

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
    database.clear_eod_snapshots(catchment)

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

        # Save market state for this day (preserving the back-dated last_updated)
        database.save_market_state(catchment, state)

        # --- 3. Revalue all open trades ---
        enriched = []
        for t in open_trade_set:
            try:
                e = delta_eng.enrich_trade(t, state)
                # Override trade_date to sim_date for new-trade P&L detection
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

    # Write hazard curve history + per-trade P&L history from all EOD snapshots
    generate_hazard_curve_history_file(catchment)
    generate_trade_pnl_history_file(catchment)

    return num_snapshots
