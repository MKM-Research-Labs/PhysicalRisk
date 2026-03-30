# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""DeltaEngine class — orchestrates delta calculations and trade revaluation."""

import logging
from typing import Dict, List, Optional

from models.hazard.prs_analytical import compute_prs_spread

from .pricer import (
    compute_risky_annuity,
    compute_gauge_delta,
    compute_basis_delta,
    compute_mark_to_market,
)

logger = logging.getLogger(__name__)


class DeltaEngine:
    """Orchestrates delta calculations and trade revaluation."""

    def __init__(self, market_state_mgr):
        """
        Args:
            market_state_mgr: MarketStateManager instance
        """
        self.market_mgr = market_state_mgr

    def enrich_trade(self, trade: Dict,
                     market_state: Optional[Dict] = None) -> Dict:
        """
        Enrich a single trade with delta and MTM calculations.

        Args:
            trade: Trade dictionary from PRS file (PhysicalSwap structure)
            market_state: Current market state (loaded if None)

        Returns:
            Enriched trade dict with gauge_delta, basis_delta, mtm, etc.
        """
        if market_state is None:
            market_state = self.market_mgr.load()

        ps = trade.get('PhysicalSwap', {})
        header = ps.get('Header', {})
        pricing = ps.get('Pricing', {})
        leg = ps.get('LegData', {})
        schedule = ps.get('ScheduleData', {})
        gauge_set = ps.get('GaugeSet', {})
        trading_meta = trade.get('TradingMetadata', {})

        swap_id = header.get('SwapID', '')
        gauge_basket = gauge_set.get('GaugeBasket', [])
        gauge_id = gauge_basket[0]['GaugeID'] if gauge_basket else ''
        gauge_name = gauge_basket[0].get('GaugeName', '') if gauge_basket else ''
        trigger = (pricing.get('TriggerLevel', 'warning') or 'warning').lower()
        notional = leg.get('Notional', 0)
        trade_status = (trading_meta.get('trade_status')
                        or header.get('TradeStatus', 'Open'))
        if trade_status.lower() == 'closed':
            original_notional = notional
            notional = 0
        else:
            original_notional = notional
        trade_spread = pricing.get('SpreadBps', 0)
        recovery = pricing.get('Recovery', 0)
        rf_rate = market_state.get('risk_free_rate', 0.03)
        yield_curve = market_state.get('yield_curve')
        is_payer = leg.get('Payer', True)

        tenor = self._remaining_tenor(schedule)

        current_rate = self.market_mgr.get_hazard_rate_for_tenor(
            market_state, gauge_id, trigger, max(tenor, 1))

        fair_spread = compute_prs_spread(
            current_rate, max(tenor, 1), recovery, rf_rate,
            yield_curve=yield_curve)

        delta_info = compute_gauge_delta(
            current_rate, max(tenor, 1), notional, recovery, rf_rate,
            yield_curve)

        risky_annuity = delta_info['risky_annuity']

        mtm = compute_mark_to_market(
            trade_spread, fair_spread, risky_annuity, notional, is_payer)

        property_id = header.get('PropertyId') or trading_meta.get('property_id')
        basis_info = {}
        if property_id:
            basis_bps = trading_meta.get('basis_bps', 0)
            basis_info = compute_basis_delta(
                current_rate, basis_bps, max(tenor, 1), notional,
                recovery, rf_rate, yield_curve)

        inception_spread_diff = (fair_spread - trade_spread) / 10000
        new_trade_pnl = inception_spread_diff * risky_annuity * notional * (
            1.0 if is_payer else -1.0)

        direction = 1.0 if is_payer else -1.0

        return {
            'swap_id': swap_id,
            'gauge_id': gauge_id,
            'gauge_name': gauge_name,
            'property_id': property_id,
            'counterparty': header.get('CounterPartyName',
                                       header.get('CounterParty', '')),
            'counterparty_id': header.get('CounterParty', ''),
            'trigger': trigger,
            'notional': notional,
            'original_notional': original_notional,
            'tenor': tenor,
            'maturity': schedule.get('EndDate', ''),
            'trade_spread_bps': trade_spread,
            'fair_spread_bps': round(fair_spread, 2),
            'is_payer': is_payer,
            'trade_date': header.get('ValuationDate', ''),
            'trade_status': trade_status,
            'close_date': trading_meta.get('close_date', ''),
            'close_spread_bps': trading_meta.get('close_spread_bps', 0),
            'final_pnl': trading_meta.get('final_pnl', 0),
            'settlement_amount': trading_meta.get('settlement_amount', 0),
            'gauge_delta_bps': delta_info['delta_spread_bps'],
            'gauge_fs01': delta_info['dv01_gbp'] * direction,
            'basis_delta_bps': basis_info.get('basis_delta_bps', 0),
            'basis_dv01': basis_info.get('basis_dv01_gbp', 0) * direction,
            'risky_annuity': risky_annuity,
            'mtm': mtm,
            'current_hazard_rate': current_rate,
            'new_trade_pnl': round(new_trade_pnl, 2),
        }

    def revalue_all(self, trades: List[Dict],
                    market_state: Optional[Dict] = None) -> List[Dict]:
        """
        Revalue all trades against current market state.

        Args:
            trades: List of PRS trade dicts
            market_state: Market state (loaded if None)

        Returns:
            List of enriched trade dicts
        """
        if market_state is None:
            market_state = self.market_mgr.load()

        return [
            self.enrich_trade(t, market_state)
            for t in trades
        ]

    def build_risk_grid(self, enriched_trades: List[Dict],
                        gauge_locations: Optional[Dict] = None) -> Dict:
        """
        Build portfolio risk grid: gauge x maturity buckets.

        Args:
            enriched_trades: List of enriched trade dicts from revalue_all()
            gauge_locations: Optional dict {gauge_id: {lat, lon, name}}
                for west-to-east ordering and gauge name display.

        Returns:
            Dict with gauges (rows), buckets (columns), cells (FS01 values)
        """
        tenor_set = set()
        grid = {}
        gauge_names = {}

        for t in enriched_trades:
            if t.get('trade_status', '').lower() == 'closed':
                continue

            gid = t.get('gauge_id', 'Unknown')
            tenor = t.get('tenor', 0)
            fs01 = t.get('gauge_fs01', 0)
            tenor_label = f'{tenor}Y'
            tenor_set.add((tenor, tenor_label))

            if gid not in grid:
                grid[gid] = {}
                if gauge_locations and gid in gauge_locations:
                    gauge_names[gid] = gauge_locations[gid].get('name', gid)
                else:
                    gauge_names[gid] = t.get('counterparty', gid)

            grid[gid][tenor_label] = grid[gid].get(tenor_label, 0.0) + fs01

        buckets = [label for _, label in sorted(tenor_set)]

        for gid in grid:
            for b in buckets:
                grid[gid].setdefault(b, 0.0)

        row_totals = {gid: sum(cells.values()) for gid, cells in grid.items()}
        col_totals = {b: sum(grid[g][b] for g in grid) for b in buckets}
        grand_total = sum(row_totals.values())

        def sort_key(gid):
            if gauge_locations and gid in gauge_locations:
                return gauge_locations[gid].get('lon', 0)
            return gid

        return {
            'buckets': buckets,
            'gauges': [
                {
                    'gauge_id': gid,
                    'gauge_name': gauge_names.get(gid, gid),
                    'cells': {b: round(grid[gid][b], 2) for b in buckets},
                    'total': round(row_totals[gid], 2),
                }
                for gid in sorted(grid.keys(), key=sort_key)
            ],
            'column_totals': {b: round(col_totals[b], 2) for b in buckets},
            'grand_total': round(grand_total, 2),
        }

    @staticmethod
    def _remaining_tenor(schedule: Dict) -> int:
        """Compute remaining tenor in whole years from schedule dates."""
        from datetime import datetime, date

        end_str = schedule.get('EndDate', '')
        if not end_str:
            return 5

        try:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            today = date.today()
            remaining = (end_date - today).days / 365.25
            return max(1, int(round(remaining)))
        except (ValueError, TypeError):
            return 5
