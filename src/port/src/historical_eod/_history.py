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

"""EOD history file writers: hazard-curve history and per-trade P&L history."""

import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


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
