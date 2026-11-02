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

"""
REIT hedge payouts attached to flooded properties.

Used by the per-storm and per-sequence portfolio-impact endpoints. The payout
rules live in ``models.trading.storm_hedges``: a hedge pays its notional when
its gauge reaches severe in the storm, not merely when the property floods.
"""

from config import config
from models.trading.storm_hedges import storm_hedge_report


def _enrich_with_prs(properties, storm_ids):
    """Attach the REIT's hedge payouts for ``storm_ids`` to each property.

    Each entry gets ``prs_trades`` (its hedges, triggered or not),
    ``prs_payout`` and ``net_pnl`` (payout less damage). Mutates
    ``properties`` in place and returns a derivatives summary dict.
    """
    report = storm_hedge_report(config.catchment_id, storm_ids)
    by_asset = {}
    for h in report['reit']['hedges']:
        by_asset.setdefault(h['asset_id'], []).append(h)

    total_payout = 0
    total_notional = 0
    num_triggered = 0
    for p in properties:
        hedges = by_asset.get(p['property_id'], [])
        payout = sum(h['payout'] for h in hedges)
        p['prs_trades'] = [{
            'swap_id': h['swap_id'],
            'notional': h['notional'],
            'payout': round(h['payout'], 2),
            'triggered': h['triggered'],
            'gauge_id': h['gauge_id'],
            'gauge_name': h['gauge_name'],
            'counterparty': h['counterparty'],
            'trade_type': h['trade_type'],
        } for h in hedges]
        p['prs_payout'] = round(payout, 2)
        p['net_pnl'] = round(payout - p['damage_amount'], 2)
        total_payout += payout
        total_notional += sum(h['notional'] for h in hedges)
        num_triggered += sum(1 for h in hedges if h['triggered'])

    total_damage = sum(p['damage_amount'] for p in properties)
    return {
        'total_prs_payout': round(total_payout, 2),
        'total_prs_notional': round(total_notional, 2),
        'num_trades_triggered': num_triggered,
        'net_portfolio_pnl': round(total_payout - total_damage, 2),
    }
