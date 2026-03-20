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
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
P&L engine for the trading desk.

Computes:
- Daily P&L: from new trades + market movements
- Running P&L: inception-to-date per trade
- EOD snapshots: daily position + P&L freeze with PDF generation

P&L decomposition:
- New trade P&L = (fair_spread - trade_spread) / 10000 * annuity * notional * dir
- Market move P&L = (today_fair - yesterday_fair) / 10000 * annuity * notional * dir
- Daily P&L = new_trade_pnl + market_move_pnl
- Running P&L = sum of all daily P&L since inception
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from .delta_engine import compute_prs_spread, compute_risky_annuity

logger = logging.getLogger(__name__)


class PnLEngine:
    """Computes and manages P&L for the trading desk."""

    def __init__(self, trading_dir: Path, prs_dir: Path):
        """
        Args:
            trading_dir: Path to data/output/trading/
            prs_dir: Path to data/output/prs/ (existing PRS trades)
        """
        self.trading_dir = Path(trading_dir)
        self.prs_dir = Path(prs_dir)
        self.eod_dir = self.trading_dir / 'eod'
        self.marks_file = self.trading_dir / 'trade_marks.json'
        self.eod_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Trade marks (supplementary data on top of PRS trade files)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # P&L calculations
    # ------------------------------------------------------------------

    def compute_daily_pnl(self, enriched_trades: List[Dict],
                          previous_eod: Optional[Dict] = None) -> Dict:
        """
        Compute daily P&L for all trades.

        Args:
            enriched_trades: Trades enriched with current marks from DeltaEngine
            previous_eod: Previous EOD snapshot (for yesterday's marks)

        Returns:
            Portfolio P&L summary
        """
        prev_marks = {}
        if previous_eod:
            for pos in previous_eod.get('positions', []):
                prev_marks[pos['swap_id']] = pos

        today_str = date.today().isoformat()
        total_daily_pnl = 0.0
        total_running_pnl = 0.0
        total_new_trade_pnl = 0.0
        total_market_pnl = 0.0
        total_realized_pnl = 0.0
        positions = []

        for t in enriched_trades:
            if t.get('trade_status', '').lower() == 'closed':
                # Include realized P&L from closed trades
                realized = t.get('final_pnl', 0)
                total_realized_pnl += realized
                continue

            swap_id = t['swap_id']
            notional = t.get('notional', 0)
            fair_spread = t.get('fair_spread_bps', 0)
            trade_spread = t.get('trade_spread_bps', 0)
            risky_annuity = t.get('risky_annuity', 0)
            is_payer = t.get('is_payer', True)
            direction = 1.0 if is_payer else -1.0

            # Is this a new trade (traded today)?
            is_new_today = t.get('trade_date', '') == today_str

            # Running P&L = full revaluation MTM from the pricing engine.
            # Use the mtm field directly if available (from DeltaEngine
            # full revaluation), otherwise compute from spread/annuity.
            running_pnl = t.get('mtm')
            if running_pnl is None:
                running_pnl = (
                    (fair_spread - trade_spread) / 10000
                    * risky_annuity * notional * direction
                )

            # Market P&L = change in full-reval MTM vs last EOD snapshot.
            # Captures ALL sources of value: hazard, yield curve, time,
            # annuity — no approximations.
            prev = prev_marks.get(swap_id, {})
            if is_new_today:
                new_trade_pnl = running_pnl
                market_pnl = 0.0
            elif prev:
                new_trade_pnl = 0.0
                prev_mtm = prev.get('running_pnl', 0)
                market_pnl = running_pnl - prev_mtm
            else:
                # Not in EOD and not new — no reference point
                new_trade_pnl = 0.0
                market_pnl = 0.0

            daily_pnl = new_trade_pnl + market_pnl

            total_daily_pnl += daily_pnl
            total_running_pnl += running_pnl
            total_new_trade_pnl += new_trade_pnl
            total_market_pnl += market_pnl

            positions.append({
                'swap_id': swap_id,
                'gauge_id': t.get('gauge_id', ''),
                'property_id': t.get('property_id'),
                'counterparty': t.get('counterparty', ''),
                'trigger': t.get('trigger', ''),
                'notional': notional,
                'tenor': t.get('tenor', 0),
                'trade_spread_bps': trade_spread,
                'fair_spread_bps': fair_spread,
                'risky_annuity': risky_annuity,
                'gauge_fs01': t.get('gauge_fs01', 0),
                'basis_dv01': t.get('basis_dv01', 0),
                'new_trade_pnl': round(new_trade_pnl, 2),
                'market_pnl': round(market_pnl, 2),
                'daily_pnl': round(daily_pnl, 2),
                'running_pnl': round(running_pnl, 2),
            })

        return {
            'date': today_str,
            'num_open_trades': len(positions),
            'total_notional': sum(p['notional'] for p in positions),
            'total_daily_pnl': round(total_daily_pnl, 2),
            'total_running_pnl': round(total_running_pnl, 2),
            'daily_pnl_from_trades': round(total_new_trade_pnl, 2),
            'daily_pnl_from_market': round(total_market_pnl, 2),
            'total_realized_pnl': round(total_realized_pnl, 2),
            'positions': positions,
        }

    # ------------------------------------------------------------------
    # EOD snapshots
    # ------------------------------------------------------------------

    def generate_eod_snapshot(self, enriched_trades: List[Dict],
                              market_state: Dict,
                              eod_date: Optional[str] = None) -> Dict:
        """
        Generate and save an EOD snapshot.

        Args:
            enriched_trades: Enriched trades from DeltaEngine
            market_state: Current market state
            eod_date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            EOD snapshot dict
        """
        if eod_date is None:
            eod_date = date.today().isoformat()

        # Load previous EOD for P&L comparison
        previous_eod = self._get_previous_eod(eod_date)

        # Compute P&L
        pnl_summary = self.compute_daily_pnl(enriched_trades, previous_eod)

        snapshot = {
            'eod_id': f"EOD-{eod_date.replace('-', '')}",
            'date': eod_date,
            'generated_at': datetime.now().isoformat(),
            'market_state_snapshot': {
                'risk_free_rate': market_state.get('risk_free_rate', 0.03),
                'gauge_adjustments': market_state.get(
                    'gauge_adjustments', {}),
                'yield_curve': market_state.get('yield_curve', {}),
                'hazard_term_structure': market_state.get(
                    'hazard_term_structure', {}),
            },
            'portfolio_summary': {
                'num_open_trades': pnl_summary['num_open_trades'],
                'total_notional': pnl_summary['total_notional'],
                'total_daily_pnl': pnl_summary['total_daily_pnl'],
                'total_running_pnl': pnl_summary['total_running_pnl'],
                'daily_pnl_from_trades': pnl_summary[
                    'daily_pnl_from_trades'],
                'daily_pnl_from_market': pnl_summary[
                    'daily_pnl_from_market'],
            },
            'positions': pnl_summary['positions'],
        }

        # Save snapshot
        snapshot_path = self.eod_dir / f"EOD-{eod_date.replace('-', '')}.json"
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)

        logger.info("EOD snapshot saved: %s", snapshot_path)
        return snapshot

    def _get_previous_eod(self, current_date: str) -> Optional[Dict]:
        """Find the most recent EOD snapshot before the given date."""
        eod_files = sorted(self.eod_dir.glob('EOD-*.json'), reverse=True)
        current_id = f"EOD-{current_date.replace('-', '')}"

        for f in eod_files:
            if f.stem <= current_id:
                with open(f) as fh:
                    return json.load(fh)

        return None

    def get_eod_history(self) -> List[Dict]:
        """Get list of all EOD snapshots (summaries only)."""
        history = []
        for f in sorted(self.eod_dir.glob('EOD-*.json'), reverse=True):
            with open(f) as fh:
                snapshot = json.load(fh)
            summary = snapshot.get('portfolio_summary', {})
            eod_date = snapshot.get('date', '')
            # Check if PDF exists for this EOD
            pdf_name = f"EOD-{eod_date.replace('-', '')}.pdf"
            has_pdf = (self.eod_dir / pdf_name).exists()
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
        """Load a specific EOD snapshot by date."""
        snapshot_path = (
            self.eod_dir / f"EOD-{eod_date.replace('-', '')}.json"
        )
        if snapshot_path.exists():
            with open(snapshot_path) as f:
                return json.load(f)
        return None

    def get_pnl_series(self) -> List[Dict]:
        """
        Get time series of daily P&L for charting.

        Returns:
            List of {date, daily_pnl, running_pnl} dicts, chronological.
        """
        series = []
        for f in sorted(self.eod_dir.glob('EOD-*.json')):
            with open(f) as fh:
                snapshot = json.load(fh)
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
