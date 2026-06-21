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

"""Daily P&L computation and EOD-snapshot generation mixin."""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import database

logger = logging.getLogger(__name__)


class _PnLComputeMixin:
    """Daily P&L decomposition and EOD snapshot writing."""

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
            elif not previous_eod:
                # First-ever EOD — no prior snapshot exists.
                # Treat entire MTM as market move (opening-day mark).
                new_trade_pnl = 0.0
                market_pnl = running_pnl
            else:
                # Trade exists in book but wasn't in previous EOD
                # (e.g. back-dated trade) — no reference point
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

        # Persist the snapshot through the database seam (keyed by EOD date).
        database.save_eod_snapshot(self.catchment, eod_date, snapshot)

        logger.info("EOD snapshot saved for catchment %s: %s", self.catchment, eod_date)
        return snapshot

    def _get_previous_eod(self, current_date: str) -> Optional[Dict]:
        """Find the most recent EOD snapshot on or before the given date."""
        for snapshot in sorted(database.iter_eod_snapshots(self.catchment),
                               key=lambda s: s.get('date', ''), reverse=True):
            if snapshot.get('date', '') <= current_date:
                return snapshot
        return None
