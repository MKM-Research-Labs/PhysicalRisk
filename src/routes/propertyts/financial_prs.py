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
PRS trade loading, property matching, and portfolio enrichment.

Used by the per-storm and per-sequence portfolio-impact endpoints to
attach PRS derivative payouts to flooded properties.
"""

import json
import logging

from config import config

logger = logging.getLogger(__name__)


def _load_all_prs_trades():
    """Load all PRS trades (PropertyPRS and inter-dealer).

    Returns a list of flat dicts with swap_id, gauge_id, property_id,
    notional, is_payer, trigger, spread_bps, counterparty, trade_type.
    """
    prs_dir = config.get_reports_dir('prs')
    if not prs_dir.exists():
        return []

    trades = []
    for f in sorted(prs_dir.glob('*PRS-*.json')):
        try:
            with open(f) as fh:
                raw = json.load(fh)
            ps = raw.get('PhysicalSwap', {})
            header = ps.get('Header', {})
            leg = ps.get('LegData', {})
            pricing = ps.get('Pricing', {})
            gauge_set = ps.get('GaugeSet', {})
            prop_set = ps.get('PropertySet', {})

            gauge_basket = gauge_set.get('GaugeBasket', [])
            gauge_id = gauge_basket[0].get('GaugeID', '') if gauge_basket else ''

            trades.append({
                'swap_id': header.get('SwapID', ''),
                'trade_type': header.get('TradeType', 'PRS'),
                'counterparty': header.get('CounterPartyName', ''),
                'is_payer': leg.get('Payer', True),
                'notional': leg.get('Notional', 0),
                'trigger': pricing.get('TriggerLevel', 'severe'),
                'spread_bps': pricing.get('SpreadBps', 0),
                'gauge_id': gauge_id,
                'property_id': prop_set.get('PropertyID', ''),
            })
        except Exception as e:
            logger.warning('Skipping PRS file %s: %s', f.name, e)
    return trades


def _match_prs_to_properties(prs_trades, property_ids, property_gauges):
    """Match PRS trades to properties.

    Returns {property_id: [trade, ...]} mapping.

    Matching rules:
    - Direct: trade.property_id == property_id
    - Gauge: trade.gauge_id in property's reference gauges
    """
    by_prop = {}
    by_gauge = {}
    for t in prs_trades:
        if t['property_id']:
            by_prop.setdefault(t['property_id'], []).append(t)
        if t['gauge_id']:
            by_gauge.setdefault(t['gauge_id'], []).append(t)

    result = {pid: [] for pid in property_ids}
    for pid in property_ids:
        # Direct match
        if pid in by_prop:
            result[pid].extend(by_prop[pid])
        # Gauge match (avoid duplicates)
        seen = {t['swap_id'] for t in result[pid]}
        for gid in property_gauges.get(pid, []):
            for t in by_gauge.get(gid, []):
                if t['swap_id'] not in seen:
                    result[pid].append(t)
                    seen.add(t['swap_id'])
    return result


def _enrich_with_prs(properties, prop_details):
    """Enrich property entries with PRS derivative payouts.

    For each flooded property, finds matching PRS trades and computes
    the REIT payout (positive = protection received).

    Mutates ``properties`` in place and returns a derivatives summary dict.
    """
    prs_trades = _load_all_prs_trades()
    if not prs_trades:
        for p in properties:
            p['prs_trades'] = []
            p['prs_payout'] = 0
            p['net_pnl'] = -p['damage_amount']
        return {
            'total_prs_payout': 0,
            'total_prs_notional': 0,
            'num_trades_triggered': 0,
            'net_portfolio_pnl': -sum(p['damage_amount'] for p in properties),
        }

    # Build property → gauge mapping from property details
    property_gauges = {}
    for pid, d in prop_details.items():
        property_gauges[pid] = d.get('reference_gauges', [])

    prop_ids = [p['property_id'] for p in properties]
    matched = _match_prs_to_properties(prs_trades, prop_ids, property_gauges)

    total_prs_payout = 0
    total_prs_notional = 0
    num_triggered = 0

    for p in properties:
        pid = p['property_id']
        trades_for_prop = matched.get(pid, [])
        prs_entries = []
        prop_payout = 0

        for t in trades_for_prop:
            # REIT is payer (buys protection) → receives +notional on trigger
            # Trader is receiver (sells protection) → pays out notional
            notional = t['notional']
            payout = notional  # full binary payout on flood
            prop_payout += payout
            total_prs_notional += notional
            num_triggered += 1
            prs_entries.append({
                'swap_id': t['swap_id'],
                'notional': notional,
                'payout': round(payout, 2),
                'trigger': t['trigger'],
                'counterparty': t['counterparty'],
                'trade_type': t['trade_type'],
            })

        p['prs_trades'] = prs_entries
        p['prs_payout'] = round(prop_payout, 2)
        p['net_pnl'] = round(prop_payout - p['damage_amount'], 2)
        total_prs_payout += prop_payout

    total_damage = sum(p['damage_amount'] for p in properties)
    return {
        'total_prs_payout': round(total_prs_payout, 2),
        'total_prs_notional': round(total_prs_notional, 2),
        'num_trades_triggered': num_triggered,
        'net_portfolio_pnl': round(total_prs_payout - total_damage, 2),
    }
