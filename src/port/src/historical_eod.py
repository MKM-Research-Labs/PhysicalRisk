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
Historical EOD series generator.

Simulates 3 months (~63 business days) of trading history:
1. Starts with an empty portfolio
2. Adds trades one-at-a-time from the book (one per day up to ~50)
3. Applies a random walk to hazard term structures each day
4. Saves market state, revalues all open trades, generates EOD snapshots

This produces realistic daily P&L, running P&L, and curve history data
for the Curves tab and EOD P&L charts.
"""

import json
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

from config.port import DAILY_HAZARD_VOL, MAX_TOTAL_MOVE, NUM_BUSINESS_DAYS


def _business_days(start: date, count: int) -> List[date]:
    """Generate a list of business days (Mon-Fri) ending at start."""
    days = []
    d = start
    while len(days) < count:
        d -= timedelta(days=1)
        if d.weekday() < 5:  # Mon=0, Fri=4
            days.append(d)
    days.reverse()
    return days


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


def generate_hazard_curve_history_file(eod_dir: Path, output_path: Path) -> None:
    """Build and write hazard_curve_history.json from all EOD snapshots.

    Output structure:
        {
          "metadata": { "num_snapshots": N, "gauges": [...], ... },
          "history": {
            "GAUGE-xxx": {
              "severe": [{"date": "YYYY-MM-DD", "1": r, "2": r, ...}, ...],
              "warning": [...],
              "alert":   [...]
            },
            ...
          }
        }
    """
    from datetime import datetime as _dt

    eod_files = sorted(Path(eod_dir).glob('EOD-*.json'))
    if not eod_files:
        return

    # gauge_id -> trigger -> [{"date": ..., "1": ..., ...}]
    history: Dict[str, Dict[str, List[Dict]]] = {}
    all_gauges: set = set()
    all_triggers: set = set()

    for f in eod_files:
        with open(f) as fh:
            snapshot = json.load(fh)
        date_str = snapshot.get('date', '')
        ts = snapshot.get('market_state_snapshot', {}).get('hazard_term_structure', {})

        for gauge_id, triggers in ts.items():
            all_gauges.add(gauge_id)
            if gauge_id not in history:
                history[gauge_id] = {}
            for trigger, tenors in triggers.items():
                all_triggers.add(trigger)
                if trigger not in history[gauge_id]:
                    history[gauge_id][trigger] = []
                entry = {'date': date_str}
                entry.update({k: v for k, v in sorted(tenors.items(), key=lambda x: int(x[0]))})
                history[gauge_id][trigger].append(entry)

    output = {
        'metadata': {
            'generated_at': _dt.now().isoformat(),
            'num_snapshots': len(eod_files),
            'gauges': sorted(all_gauges),
            'triggers': sorted(all_triggers),
            'description': (
                'Daily hazard term structure per gauge/trigger extracted '
                'from EOD snapshots. Random-walk evolution: 2bp daily vol, '
                '20bp max cumulative move from base.'
            ),
        },
        'history': history,
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info("Hazard curve history written: %s (%d gauges, %d snapshots)",
                output_path.name, len(all_gauges), len(eod_files))


def generate_trade_pnl_history_file(eod_dir: Path, output_path: Path) -> None:
    """Build and write trade_pnl_history.json from all EOD snapshots.

    For each trade, records a vector of daily EOD marks, market P&L and
    running P&L — one entry per EOD day the trade was open.  The first
    trade added to the book has 63 entries, the second 62, and so on.

    Output structure:
        {
          "metadata": { "num_snapshots": N, "num_trades": M, ... },
          "trades": {
            "PRS-xxx": {
              "trade_date": "YYYY-MM-DD",
              "trade_spread_bps": 210.0,
              "gauge_id": "GAUGE-xxx",
              "trigger": "severe",
              "notional": 10000000,
              "is_payer": true,
              "history": [
                {"date": "YYYY-MM-DD", "mark": 206.4,
                 "mkt_pnl": 1200.0, "running_pnl": 24176.0},
                ...
              ]
            },
            ...
          }
        }
    """
    from datetime import datetime as _dt

    eod_files = sorted(Path(eod_dir).glob('EOD-*.json'))
    if not eod_files:
        return

    # trade_id -> {meta, history list}
    trades: Dict[str, dict] = {}

    for f in eod_files:
        with open(f) as fh:
            snapshot = json.load(fh)
        date_str = snapshot.get('date', '')
        positions = snapshot.get('positions', [])

        for pos in positions:
            swap_id = pos.get('swap_id', '')
            if not swap_id:
                continue

            if swap_id not in trades:
                trades[swap_id] = {
                    'trade_date': pos.get('trade_date', ''),
                    'trade_spread_bps': pos.get('trade_spread_bps', 0),
                    'gauge_id': pos.get('gauge_id', ''),
                    'trigger': pos.get('trigger', ''),
                    'notional': pos.get('notional', 0),
                    'is_payer': pos.get('is_payer', True),
                    'history': [],
                }

            trades[swap_id]['history'].append({
                'date': date_str,
                'mark': pos.get('fair_spread_bps', 0),
                'mkt_pnl': pos.get('market_pnl', 0),
                'running_pnl': pos.get('running_pnl', 0),
            })

    output = {
        'metadata': {
            'generated_at': _dt.now().isoformat(),
            'num_snapshots': len(eod_files),
            'num_trades': len(trades),
            'description': (
                'Per-trade EOD mark, market P&L and running P&L vectors. '
                'Mark = fair_spread_bps revalued against the day hazard curve. '
                'Mkt P&L = change in MTM from previous EOD (hazard curve move). '
                'Running P&L = cumulative MTM from trade inception.'
            ),
        },
        'trades': trades,
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    history_lengths = [len(t['history']) for t in trades.values()]
    logger.info(
        "Trade P&L history written: %s (%d trades, history lengths %d-%d)",
        output_path.name, len(trades),
        min(history_lengths) if history_lengths else 0,
        max(history_lengths) if history_lengths else 0,
    )
