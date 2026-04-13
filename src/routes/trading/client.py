# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Client (property PRS) blotter endpoint."""

import json
import logging
from typing import List

from flask import jsonify

from config import config
from . import trading_bp

logger = logging.getLogger(__name__)


def _load_property_trades() -> List[dict]:
    """Load all property PRS trades (those with a PropertySet section).

    Returns flat dicts suitable for both the client blotter and aggregate map.
    """
    prs_dir = config.get_reports_dir("prs")
    prs_dir.mkdir(parents=True, exist_ok=True)

    trades = []
    for f in sorted(prs_dir.glob("*PRS-*.json")):
        try:
            with open(f) as fh:
                trade = json.load(fh)

            ps = trade.get('PhysicalSwap', {})
            if 'PropertySet' not in ps:
                continue

            header = ps.get('Header', {})
            leg = ps.get('LegData', {})
            schedule = ps.get('ScheduleData', {})
            prop = ps.get('PropertySet', {})
            pricing = ps.get('Pricing', {})
            gauge_set = ps.get('GaugeSet', {})

            notional = leg.get('Notional', 0)
            risky_annuity = pricing.get('RiskyAnnuity', 0)
            is_payer = leg.get('Payer', False)
            sign = 1 if is_payer else -1

            property_value = prop.get('PropertyValue', 0)
            hedge_ratio = (
                round(notional / property_value * 100, 1)
                if property_value > 0 else 0
            )

            trades.append({
                'swap_id': header.get('SwapID', ''),
                'trade_type': header.get('TradeType', ''),
                'counterparty': header.get('CounterPartyName', ''),
                'counterparty_id': header.get('CounterParty', ''),
                'trade_date': header.get('ValuationDate', ''),
                'trade_status': header.get('TradeStatus', 'Committed'),
                'is_payer': is_payer,
                'currency': leg.get('Currency', 'GBP'),
                'notional': notional,
                'tenor': schedule.get('Tenor', ''),
                'start_date': schedule.get('StartDate', ''),
                'end_date': schedule.get('EndDate', ''),
                'property_id': prop.get('PropertyID', ''),
                'property_address': prop.get('PropertyAddress', ''),
                'postcode': prop.get('Postcode', ''),
                'local_authority': prop.get('LocalAuthority', ''),
                'ea_flood_zone': prop.get('EAFloodZone', ''),
                'latitude': prop.get('Latitude', 0),
                'longitude': prop.get('Longitude', 0),
                'reference_gauge': prop.get('ReferenceGauge', ''),
                'spread_bps': pricing.get('SpreadBps', 0),
                'fair_spread_bps': pricing.get('FairSpreadBps', 0),
                'npv': pricing.get('NPV', 0),
                'trigger_level': pricing.get('TriggerLevel', ''),
                'gauge_fs01': sign * notional * risky_annuity * 0.0001,
                'gauge_id': (gauge_set.get('GaugeBasket', [{}])[0]
                             .get('GaugeID', '')
                             if gauge_set.get('GaugeBasket') else ''),
                # Trader perspective: Trader is always receiver on PropertyPRS
                'trader_direction': 'Rcv',
                'property_value': property_value,
                'hedge_ratio': hedge_ratio,
            })
        except Exception as e:
            logger.warning("Skipping trade file %s: %s", f.name, e)
            continue

    return trades


@trading_bp.route("/trading/client", methods=["GET"])
def get_client_blotter():
    """Get all property PRS trades for the client blotter tab."""
    try:
        trades = _load_property_trades()

        total_notional = sum(t['notional'] for t in trades)
        total_property_value = sum(t['property_value'] for t in trades)
        spreads = [t['spread_bps'] for t in trades if t['spread_bps'] > 0]
        avg_spread = round(sum(spreads) / len(spreads), 1) if spreads else 0

        return jsonify({
            'status': 'success',
            'trades': trades,
            'summary': {
                'num_trades': len(trades),
                'total_notional': total_notional,
            },
            'trader_summary': {
                'total_notional_sold': total_notional,
                'avg_spread_collected': avg_spread,
                'total_property_value_covered': total_property_value,
                'num_trades': len(trades),
            },
        })

    except Exception as e:
        logger.error("Client blotter error: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500
